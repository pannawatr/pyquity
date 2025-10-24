import pyquity
import osmnx as ox
import numpy as np
import networkx as nx

class Equity:
    def __init__(self, G, grid, amenity):
        self.G = G
        self.grid = grid
        self.amenity = amenity

        # Ensure amenities are point geometries
        if not all(self.amenity.geometry.geom_type == "Point"):
            self.amenity["geometry"] = self.amenity.geometry.centroid

    def sufficientarianism(self, served_time: int=15):
        # Map amenities to nearest nodes
        self.amenity_nodes = ox.distance.nearest_nodes(self.G, self.amenity.geometry.centroid.x.values, self.amenity.geometry.centroid.y.values)

        # Map grid centroids to nearest nodes
        self.grid_nodes = ox.distance.nearest_nodes(self.G, self.grid.geometry.centroid.x.values, self.grid.geometry.centroid.y.values)

        # Assign the nearest network node ID to each grid cell and Intialize served column
        self.grid['grid_id'] = self.grid_nodes
        self.grid["served"] = 0

        # Iterate over each grid node
        for grid_node in self.grid_nodes:
            if self.grid.loc[self.grid["grid_id"] == grid_node, "served"].iloc[0] == 1:
                continue

            # Compute shortest paths from this grid node to all other nodes
            paths = nx.single_source_dijkstra_path(self.G, source=int(grid_node), weight='length', cutoff=served_time * (22 * 1000 / 3600) * 60)

             # Iterate over each amenity node
            for amenity_node in self.amenity_nodes:
                # If this grid node is already served, no need to check further amenities
                if self.grid.loc[self.grid["grid_id"] == grid_node, "served"].values[0] == 1:
                    break
                
                # Check if the amenity is reachable in the computed paths
                if amenity_node in paths:
                    try:
                        # Get the route as a list of node IDs and Calculate distance and travel time for this route using pyquity
                        route = [int(node) for node in paths[int(amenity_node)]]
                        distance, travel_time = pyquity.route_length_by_mode(self.G, route)
                        total_time = sum(travel_time.values())

                        # If total travel time is within the served_time threshold
                        if total_time <= served_time:
                            self.grid.loc[self.grid["grid_id"] == grid_node, "served"] = 1
                            print(int(grid_node), int(amenity_node), distance, total_time, paths[int(amenity_node)])
                            break
                    except:
                        continue

        # Return GeoDataFrame of grid
        return self.grid
