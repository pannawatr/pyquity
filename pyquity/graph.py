import osmnx as ox
import numpy as np
import pandas as pd
import networkx as nx
import geopandas as gpd
import partridge as ptg
from geopy.distance import geodesic
from shapely.geometry import Polygon

def graph_from_gtfs(gtfs: str) -> nx.DiGraph:
    # Read service dates from GTFS
    date = ptg.read_service_ids_by_date(gtfs)
    if not date:
        raise ValueError("No valid service date found in GTFS.")

    # Select the service date and Load GTFS feed
    target_date = sorted(date.keys())[0]
    feed = ptg.load_geo_feed(gtfs, view={'trips.txt': {'service_id': date[target_date]}, 'shapes.txt': {}})
    
    # Extract GTFS tables
    stop_times = feed.stop_times
    trips = feed.trips
    stops = feed.stops
    shapes = feed.shapes

    # Initialize a directed graph
    G = nx.DiGraph()

    # Add each transit stop as a node in the graph
    coords = {}
    for _, row in stops.iterrows():
        coords[row['stop_id']] = (row['geometry'].y, row['geometry'].x)
        G.add_node(row['stop_id'], name=row['stop_name'], lat=row['geometry'].y, lon=row['geometry'].x)
    
    # Loop through each trip in the feed to construct edges
    for trip_id in trips['trip_id']:
        trip_stops = stop_times[stop_times.trip_id == trip_id].sort_values('stop_sequence')

        prev_stop = None
        prev_departure = None

        # Loop through each stop in the trip
        for _, row in trip_stops.iterrows():
            stop_id = row['stop_id']
            departure_time = row['departure_time']
            arrival_time = row['arrival_time']

            # If this isn't the first stop in the trip and time data is valid
            if prev_stop and pd.notnull(prev_departure) and pd.notnull(arrival_time):
                travel_time = arrival_time - prev_departure  # Compute travel time in seconds

                if travel_time >= 0:
                    # Calculate the geographic distance between the two stops in meters
                    distance_m = geodesic(stop_coords[prev_stop], stop_coords[stop_id]).meters
                    print(distance_m)


    # Return a directed graph
    return G

def graph_from_place(place_name: str, network_type: str) -> gpd.GeoDataFrame:
    # Return a graph from OSMnx
    return ox.graph_from_place(place_name, network_type=network_type)

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