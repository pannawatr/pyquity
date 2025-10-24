import pyquity
import osmnx as ox
import numpy as np
import networkx as nx

class Equity:
    def __init__(self, G_walk, G_micromobility, grid, amenity):
        self.G_walk = G_walk
        self.G_micromobility = G_micromobility
        self.grid = grid
        self.amenity = amenity

        # Ensure amenities are point geometries
        if not all(self.amenity.geometry.geom_type == "Point"):
            self.amenity["geometry"] = self.amenity.geometry.centroid

    def sufficientarianism(self, served_time: int = 15):
        # Map amenities to nearest nodes and map grid centroids to nearest nodes with micromobility
        self.micromobility_amenity_nodes = ox.distance.nearest_nodes(self.G_micromobility, self.amenity.geometry.centroid.x.values, self.amenity.geometry.centroid.y.values)
        self.micromobility_grid_nodes = ox.distance.nearest_nodes(self.G_micromobility, self.grid.geometry.centroid.x.values, self.grid.geometry.centroid.y.values)

        # Map amenities to nearest nodes and map grid centroids to nearest nodes with walk
        self.walk_amenity_nodes = ox.distance.nearest_nodes(self.G_walk, self.amenity.geometry.centroid.x.values, self.amenity.geometry.centroid.y.values)
        self.walk_grid_nodes = ox.distance.nearest_nodes(self.G_walk, self.grid.geometry.centroid.x.values, self.grid.geometry.centroid.y.values)

        # Assign the nearest network node ID to each grid cell based on micromobility count
        self.grid["grid_id"] = np.where(self.grid['micromobility_count'] > 0, self.micromobility_grid_nodes, self.walk_grid_nodes)
        self.grid["served"] = 0

        # Iterate over each grid row to calculate serviceability
        for idx, grid_row in self.grid.iterrows():
            grid_node = grid_row['grid_id']

            # Check if the grid has micromobility services or not and select the appropriate graph and nodes
            if grid_row['micromobility_count'] > 0:
                G_current = self.G_micromobility
                amenity_nodes = self.micromobility_amenity_nodes
            else:
                G_current = self.G_walk
                amenity_nodes = self.walk_amenity_nodes

            # Compute shortest paths from the selected grid node to all other nodes
            paths = nx.single_source_dijkstra_path(G_current, source=grid_node, weight='length', cutoff=served_time * (22 * 1000 / 3600) * 60)

            # Iterate over each amenity node to check if it's reachable within the time limit
            for amenity_node in amenity_nodes:
                # If this grid node is already served, no need to check further amenities
                if self.grid.loc[self.grid["grid_id"] == grid_node, "served"].values[0] == 1:
                    break

                # Check if the amenity is reachable in the computed paths
                if amenity_node in paths:
                    try:
                        # Get the route as a list of node IDs and calculate distance and travel time using pyquity
                        route = [int(node) for node in paths[int(amenity_node)]]
                        distance, travel_time = pyquity.route_length_by_mode(G_current, route)
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
