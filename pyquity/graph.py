import osmnx as ox
import pandas as pd
import networkx as nx
import partridge as ptg
from math import radians, cos, sin, asin, sqrt

def graph_from_gtfs(gtfs: str) -> nx.DiGraph:
    # Read service dates from GTFS
    date = ptg.read_service_ids_by_date(gtfs)
    if not date:
        raise ValueError("No valid service date found in GTFS.")

    # Select the service date and Load GTFS feed
    target_date = sorted(date.keys())[0]
    feed = ptg.load_geo_feed(gtfs, view={'trips.txt': {'service_id': date[target_date]}})
    
    # Extract GTFS tables
    stop_times = feed.stop_times
    trips = feed.trips
    stops = feed.stops
    
    # Initialize a directed graph
    G = nx.DiGraph()

    # Add each transit stop as a node in the graph
    for _, row in stops.iterrows():
        G.add_node(row['stop_id'], name=row['stop_name'], lat=row['geometry'].y, lon=row['geometry'].x)
    return G