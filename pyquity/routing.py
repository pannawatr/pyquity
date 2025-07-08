import osmnx as ox
import networkx as nx

def shortest_path(G, origin, destination, weight: str = 'length'):
    route = nx.dijkstra_path(G, source=origin,  target=destination, weight=weight)
    return route