import osmnx as ox
import numpy as np
import networkx as nx

class Equity:
    def __init__(self, G, grid, amenity):
        self.G = G
        self.grid = grid
        self.amenity = amenity

        # Reproject amenities to metric CRS
        self.amenity = self.amenity.to_crs(epsg=3857)

        # Ensure amenities are point geometries
        if not all(self.amenity.geometry.geom_type == "Point"):
            self.amenity["geometry"] = self.amenity.geometry.centroid

    def sufficientarianism(self, served_time: int=15):
        # Map amenities to nearest nodes
        xs = self.amenity.geometry.centroid.x.values
        ys = self.amenity.geometry.centroid.y.values
        self.amenity_nodes = ox.distance.nearest_nodes(self.G, xs, ys)

        # Map grid centroids to nearest nodes
        xs = self.grid.geometry.centroid.x.values
        ys = self.grid.geometry.centroid.y.values
        self.grid_nodes = ox.distance.nearest_nodes(self.G, xs, ys)

        return self.grid
