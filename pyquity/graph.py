import osmnx as ox
import numpy as np
import pandas as pd
import networkx as nx
import geopandas as gpd
import partridge as ptg
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
    for _, row in stops.iterrows():
        G.add_node(row['stop_id'], name=row['stop_name'], lat=row['geometry'].y, lon=row['geometry'].x)

    # Return a directed graph
    return G

def graph_from_place(place_name: str, network_type: str) -> gpd.GeoDataFrame:
    # Return a graph from OSMnx
    return ox.graph_from_place(place_name, network_type=network_type)

def grid_from_place(place_name: str, grid_size: float) -> gpd.GeoDataFrame:
    # Read boundary from OpenStreetMap(OSM)
    boundary = ox.geocode_to_gdf(place_name)
    boundary = boundary.to_crs(epsg=3857) # Convert EPSG:4326 to EPSG:3857
    minx, miny, maxx, maxy = boundary.total_bounds

    # Initialize a grid and Add into GeoDataFrame 
    polygons = [Polygon([(x, y), (x + grid_size, y), (x + grid_size, y + grid_size), (x, y + grid_size)]) for x in np.arange(minx, maxx, grid_size) for y in np.arange(miny, maxy, grid_size)]
    gdf = gpd.GeoDataFrame(geometry=polygons, crs=boundary.crs)
    grid = gpd.overlay(gdf, boundary, how='intersection')

    # Return a grid
    return grid.to_crs(epsg=4326)