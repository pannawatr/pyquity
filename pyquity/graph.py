import osmnx as ox
import numpy as np
import pandas as pd
import networkx as nx
import geopandas as gpd
import partridge as ptg
from shapely import ops as sops
from scipy.spatial import cKDTree
from geopy.distance import distance
from shapely.geometry import Point, Polygon, LineString

def multimodal_graph(G_osm: nx.MultiDiGraph, G_gtfs: nx.MultiDiGraph, k: int=1):
    # Get OSM node coordinates
    osm_nodes, _ = ox.graph_to_gdfs(G_osm)
    osm_coords = np.array(list(zip(osm_nodes["y"], osm_nodes["x"])))

    # Get GTFS stop coordinates
    gtfs_nodes = [(n, data["x"], data["y"]) for n, data in G_gtfs.nodes(data=True)]
    gtfs_coords = np.array([(y, x) for _, x, y in gtfs_nodes])

    # Build KD-tree for nearest-neighbor search
    tree = cKDTree(osm_coords)

     # Combine OSM and GTFS graphs
    G = nx.compose(G_osm, G_gtfs)

    # Connect each GTFS stop to its nearest OSM node(s)
    for (stop_id, x, y), (dist, idx) in zip(gtfs_nodes, zip(*tree.query(gtfs_coords, k=k))):
        osm_node = osm_nodes.iloc[idx].name
        point_u = (y, x)
        point_v = (osm_nodes.iloc[idx].y, osm_nodes.iloc[idx].x)

        length = distance(point_u, point_v).m
        G.add_edge(stop_id, osm_node, mode="transfer", length=length)
        G.add_edge(osm_node, stop_id, mode="transfer", length=length)

    # Return the graph
    G.graph["crs"] = "EPSG:4326"
    return G

def graph_from_gtfs(gtfs: str) -> nx.MultiDiGraph:
    # Read available service dates
    date = ptg.read_service_ids_by_date(gtfs)
    if not date:
        raise ValueError("No valid service date found in GTFS.")

    # Select the first available service date
    target_date = sorted(date.keys())[0]
    feed = ptg.load_geo_feed(gtfs, view={'trips.txt': {'service_id': date[target_date]}, 'shapes.txt': {}})

    # Extract GTFS tables
    stop_times = feed.stop_times
    trips = feed.trips
    stops = feed.stops
    shapes = feed.shapes

    # Initialize a multidirected graph
    G = nx.MultiDiGraph()

    # Add each transit stop as a node in the graph
    for _, row in stops.iterrows():
        G.add_node(row['stop_id'], name=row['stop_name'], x=row['geometry'].x, y=row['geometry'].y)

    # Ensure all shape geometries are LineString
    shapes['geometry'] = shapes['geometry'].apply( lambda geoms: geoms if isinstance(geoms, LineString) else LineString(geoms))
    shapes = shapes.set_index('shape_id').geometry

    # Create edges from trips, grouped by shape_id
    for shape_id, group in trips.groupby('shape_id'):
        if shape_id not in shapes.index or shapes[shape_id] is None:
            continue
        geoms = shapes[shape_id]

        # Take the first trip in the group as representative
        trip_id = group.iloc[0]['trip_id']

        # Get the stop sequence for the trip
        stop_sequence = stop_times[stop_times.trip_id == trip_id].sort_values('stop_sequence')
        stop_id = stop_sequence['stop_id'].tolist()

        # Add edges between consecutive stops
        for i in range(len(stop_id) - 1):
            u, v = stop_id[i], stop_id[i + 1]

            # Retrieve the coordinates of the two stops
            point_u = stops.loc[stops.stop_id == u, 'geometry'].values[0]
            point_v = stops.loc[stops.stop_id == v, 'geometry'].values[0]
            length = distance((point_u.y, point_u.x), (point_v.y, point_v.x)).m

            # Get geometry for the edge
            try:
                orig = geoms.project(point_u)
                dest = geoms.project(point_v)
                low, high = sorted([orig, dest])
                segment = sops.substring(geoms, low, high, normalized=False)
                if segment.is_empty or segment.length == 0:
                    segment = LineString([pu, pv])
            except:
                LineString([point_u, point_v])

            # Add edge only if it does not already exist, and add geometry
            if not G.has_edge(u, v, key=trip_id):
                G.add_edge(
                    u, v,
                    trip_id=trip_id,
                    geometry=segment,
                    length=length,
                    mode='transit'
                )

    # Return the graph
    G.graph['crs'] = "EPSG:4326"
    return G

def graph_from_place(place_name: str, network_type: str):
    # Return a graph from OSMnx
    G = ox.graph_from_place(place_name, network_type=network_type)

    # Add mode to each edge in the graph
    for u, v, k, data in G.edges(keys=True, data=True):
        data['mode'] = network_type

    return G

def grid_from_place(place_name: str, grid_size: float) -> gpd.GeoDataFrame:
    # Read boundary from OpenStreetMap(OSM)
    boundary = ox.geocode_to_gdf(place_name)
    boundary = boundary.to_crs(epsg=3857) # Project boundary to Web Mercator(EPSG:3857) from default(EPSG:4326)
    minx, miny, maxx, maxy = boundary.total_bounds

    # Initialize a grid and Add into GeoDataFrame 
    polygons = [Polygon([(x, y), (x + grid_size, y), (x + grid_size, y + grid_size), (x, y + grid_size)]) for x in np.arange(minx, maxx, grid_size) for y in np.arange(miny, maxy, grid_size)]
    gdf = gpd.GeoDataFrame(geometry=polygons, crs=boundary.crs)
    grid = gpd.overlay(gdf, boundary, how='intersection')

    # Reproject the grid back to WGS84 (EPSG:4326) and return it
    return grid.to_crs(epsg=4326)

def amenity_from_place(place_name: str, amenity_type: str) -> gpd.GeoDataFrame:
    # Define categories of amenities with their corresponding OSM tags
    amenity = {
        'education': ['college', 'dancing_school', 'driving_school', 'first_aid_school', 'kindergarten', 'language_school', 'library', 'surf_school', 'toy_library', 'research_institute', 'training', 'music_school', 'school', 'traffic_park', 'university'],
        'financial': ['atm', 'bank', 'bureau_de_change'],
        'healthcare': ['baby_hatch', 'clinic', 'dentist', 'doctors', 'hospital', 'nursing_home', 'pharmacy', 'social_facility', 'veterinary' ]
        }
    
    # Get the list of amenity tags for the selected amenity type
    amenity = amenity[amenity_type.lower()]

    # Query OpenStreetMap for features matching the selected amenity tags within the specified place
    gdf = ox.features.features_from_place(place_name, tags={'amenity': amenity})

    # Return the resulting GeoDataFrame
    return gdf

def amenity_in_grid(grid: gpd.GeoDataFrame, amenity: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    # Reproject amenities to Web Mercator (EPSG:3857) and convert geometry to centroids (points)
    amenity = amenity.to_crs(epsg=3857)
    amenity['geometry'] = amenity.geometry.centroid

    # Reproject grid to Web Mercator
    grid = grid.to_crs(epsg=3857)

    # Ensure both layers have the same CRS before spatial operations
    if grid.crs == amenity.crs:
        grid['amenity_count'] = 0 # Initialize 'amenity_count' column in the grid

        # Count amenities within each grid cell
        for index, x in grid.iterrows():
            for _, y in amenity.iterrows():
                if x.geometry.contains(y.geometry): 
                    grid.at[index, 'amenity_count'] += 1
    
    # Reproject the grid back to WGS84 (EPSG:4326) and return it
    return grid.to_crs(epsg=4326)

def micromobility_in_grid(grid: gpd.GeoDataFrame, amenity: gpd.GeoDataFrame, micromobility_size: int) -> gpd.GeoDataFrame:
    # Calculate and normalize initial weight based on number of POIs relative to total amenities
    if 'amenity_count' in grid.columns:
        weight = grid['amenity_count'] / len(amenity)
        weight = weight / weight.sum()
        raws = weight / micromobility_size

        # Assign the floor of the allocation to ensure integer values
        grid['micromobility_count'] = raws.apply(np.floor).astype(int)

        # Calculate the remaining micromobility units that need to be distributed
        remainder = micromobility_size - grid['micromobility_count'].sum()
        fractional = raws - np.floor(raws)

        # Distribute the remaining units to the grid cells with the highest fractional values
        indices = fractional.sort_values(ascending=False).index[:remainder]
        for index in indices:
            grid.at[index, 'micromobility_count'] += 1
        
        # Return the updated grid
        return grid

"""
def graph_to_gdf(G: nx.MultiDiGraph or nx.MultiGraph) -> gpd.GeoDataFrame or tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    if G.nodes is not None:
        # Extract node ids and their attribute dictionaries
        uvk, data = zip(*G.nodes(data=True))

        # Build geometry for each node as a shapely Point and create a GeoDataFrame for nodes with geometry as Point
        geometry = (Point(x['y'], x['x']) for x in data)
        gdf_nodes = gpd.GeoDataFrame(data, index=uvk, crs='EPSG:4326', geometry=list(geometry))

        # Rename the node index to "gtfsid" (instead of default integer index)
        gdf_nodes.index = gdf_nodes.index.rename("gtfsid")

    if G.edges is not None:
        # Extract u (source), v (target), k (edge key) and attributes of edges
        u, v, k, data = zip(*G.edges(keys=True, data=True))

        # Prepare node coordinates dictionary {node_id: (lat, lon)}
        coords = {x: (G.nodes[x]['y'], G.nodes[x]['x']) for x in G}

        # If edge already has geometry (like a polyline from OSM), use it. Otherwise, create a straight LineString from coordinates of u and v
        geometry = (data.get('geometry', LineString((coords[u], coords[v]))) for u, v, _, data in G.edges(keys=True, data=True))

        # Create a GeoDataFrame for edges with geometry as LineString
        gdf_edges = gpd.GeoDataFrame(data, crs='EPSG:4326', geometry=list(geometry))

        # Add columns for u, v, and key (so edges can be uniquely identified)
        gdf_edges["u"] = u
        gdf_edges["v"] = v
        gdf_edges["key"] = k

        # Set the index of the GeoDataFrame to (u, v, key)
        gdf_edges = gdf_edges.set_index(["u", "v", "key"])
    
    # Return both GeoDataFrames
    return gdf_nodes, gdf_edges
"""