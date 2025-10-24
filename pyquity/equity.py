import pyquity
import osmnx as ox
import numpy as np
import networkx as nx

class Equity:
    def __init__(self, G, grid, amenity):
        self.G = G
        self.grid = grid.to_crs(epsg=3857)
        self.amenity = amenity.to_crs(epsg=3857)

        # Ensure amenities are point geometries
        if not all(self.amenity.geometry.geom_type == "Point"):
            self.amenity["geometry"] = self.amenity.geometry.centroid

    def sufficientarianism(self, served_time: int=15):
        # Map amenities to nearest nodes
        self.amenity_nodes = ox.distance.nearest_nodes(self.G, self.amenity.geometry.centroid.x.values, self.amenity.geometry.centroid.y.values)

        # Map grid centroids to nearest nodes
        self.grid_nodes = ox.distance.nearest_nodes(self.G, self.grid.geometry.centroid.x.values, self.grid.geometry.centroid.y.values)

        # Return GeoDataFrame of grid
        return self.grid.to_crs(epsg=4326)
