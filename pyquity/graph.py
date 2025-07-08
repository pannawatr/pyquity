import osmnx as ox
import numpy as np
import pandas as pd
import networkx as nx
import partridge as ptg
import geopandas as gpd

from tqdm import tqdm
from shapely.geometry import Polygon, Point, LineString

# Ref: Base on OSMnx 
def graph_from_place(place_name: str, network_type: str='all'):
    return ox.graph_from_place(place_name, network_type=network_type)

def graph_from_gtfs(gtfs_file: str) -> nx.DiGraph:
    date = ptg.read_service_ids_by_date(gtfs_file)
    if not date:
        raise ValueError("No valid service date found in GTFS file")
    target_date = sorted(date.keys())[0]
    feed = ptg.load_geo_feed(gtfs_file, view={'trips.txt': {'service_id': date[target_date]}})

    stop_times = feed.stop_times
    trips = feed.trips
    stops = feed.stops

    G = nx.DiGraph()
    for _, row in stops.iterrows():
        point = row['geometry']
        G.add_node(row['stop_id'], lat=point.y, lon=point.x, name=row['stop_name'])

    for trip_id in tqdm(trips['trip_id'], desc="Create gtfs graph"):
        trip_stops = stop_times[stop_times.trip_id == trip_id].sort_values('stop_sequence')
        prev_stop = None
        prev_departure = None

        for _, row in trip_stops.iterrows():
            stop_id = row['stop_id']
            departure_time = row['departure_time']
            arrival_time = row['arrival_time']

            if prev_stop and pd.notnull(prev_departure) and pd.notnull(arrival_time):
                travel_time = arrival_time - prev_departure
                if travel_time >= 0:
                    G.add_edge(
                        prev_stop,
                        stop_id,
                        trip_id=trip_id,
                        travel_time=travel_time
                    )

            prev_stop = stop_id
            prev_departure = departure_time
    print(f"\nGraph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    return G

def grid_from_place(place_name: str, grid_size: float) -> gpd.GeoDataFrame:
    boundary = ox.geocode_to_gdf(place_name)
    boundary = boundary.to_crs(epsg=3857)
    minx, miny, maxx, maxy = boundary.total_bounds
    polygons = [Polygon([(x, y), (x + grid_size, y), (x + grid_size, y + grid_size), (x, y + grid_size)]) for x in np.arange(minx, maxx, grid_size) for y in np.arange(miny, maxy, grid_size)]
    gdf = gpd.GeoDataFrame(geometry=polygons, crs=boundary.crs)
    grid = gpd.overlay(gdf, boundary, how='intersection')
    return grid.to_crs(epsg=4326)

def get_amenity(place_name: str, amenity_type: str) -> gpd.GeoDataFrame:
    amenities = {'education': ['college', 'dancing_school', 'driving_school', 'first_aid_school', 'kindergarten', 'language_school', 'library', 'surf_school', 'toy_library', 'research_institute', 'training', 'music_school', 'school', 'traffic_park', 'university'], 'financial': ['atm', 'bank', 'bureau_de_change'], 'healthcare': ['baby_hatch', 'clinic', 'dentist', 'doctors', 'hospital', 'nursing_home', 'pharmacy', 'social_facility', 'veterinary' ]}
    amenity = amenities[amenity_type.lower()]
    gdf = ox.features.features_from_place(place_name, tags={'amenity': amenity})
    return gdf

def grid_nearest_node(G, grid: gpd.GeoDataFrame):
    nodes = [ox.distance.nearest_nodes(G, point.x, point.y) for point in tqdm(grid.geometry.centroid, desc="Find nearest node from grid to graph")]
    return nodes

def grid_poi(grid: gpd.GeoDataFrame, amenity: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    amenity = amenity.to_crs(epsg=3857)
    amenity.geometry = amenity.geometry.centroid
    amenity = amenity.to_crs(grid.crs)
    grid['poi'] = 0
    for index, x in grid.iterrows():
        for _, y in amenity.iterrows():
            if x.geometry.contains(y.geometry):
                grid.at[index, 'poi'] += 1
    return grid

def graph_to_gdf(G) -> gpd.GeoDataFrame:
    nodes = []
    for node_id, data in G.nodes(data=node):
        try:
            point = Point(data['lon'], data['lat'])
        except:
            point = Point(data['x'], data['y'])
        nodes.append({'stop_id': node_id, 'geometry': point, 'name': data.get('name', '')})
    gdf_nodes = gpd.GeoDataFrame(nodes, crs='EPSG:4326')

    edges = []
    for u, v, data in G.edges(data=edge):
        try:
            point_u = Point(G.nodes[u]['lon'], G.nodes[u]['lat'])
            point_v = Point(G.nodes[v]['lon'], G.nodes[v]['lat'])
        except:
            point_u = Point(G.nodes[u]['x'], G.nodes[u]['y'])
            point_v = Point(G.nodes[v]['x'], G.nodes[v]['y'])
        line = LineString([point_u, point_v])
        edges.append({
            'from': u,
            'to': v,
            'geometry': line,
            'trip_id': data.get('trip_id'),
            'travel_time': data.get('travel_time')
            })
    gdf_edges = gpd.GeoDataFrame(edges, crs='EPSG:4326')
    gdf = pd.concat([gdf_nodes, gdf_edges], ignore_index=True)
    return gdf

def multimodal_graph():
    return G