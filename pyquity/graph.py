import osmnx as ox
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon

def grid_from_place(place_name: str, grid_size: float) -> gpd.GeoDataFrame:
    boundary = ox.geocode_to_gdf(place_name)
    boundary = boundary.to_crs(epsg=3857)
    minx, miny, maxx, maxy = boundary.total_bounds
    polygons = [Polygon([(x, y), (x + grid_size, y), (x + grid_size, y + grid_size), (x, y + grid_size)]) for x in np.arange(minx, maxx, grid_size) for y in np.arange(miny, maxy, grid_size)]
    gdf = gpd.GeoDataFrame(geometry=polygons, crs=boundary.crs)
    gdf = gpd.overlay(gdf, boundary, how='intersection')
    return gdf.to_crs(epsg=4326)

def get_amenity(place_name: str, amenity_type: str):
    amenities = {'education': ['college', 'dancing_school', 'driving_school', 'first_aid_school', 'kindergarten', 'language_school', 'library', 'surf_school', 'toy_library', 'research_institute', 'training', 'music_school', 'school', 'traffic_park', 'university'], 'financial': ['atm', 'bank', 'bureau_de_change'], 'healthcare': ['baby_hatch', 'clinic', 'dentist', 'doctors', 'hospital', 'nursing_home', 'pharmacy', 'social_facility', 'veterinary' ]}
    amenity = amenities[amenity_type.lower()]
    gdf = ox.features.features_from_place(place_name, tags={'amenity': amenity})
    return gdf

def grid_nearest_node(graph, grid):
    nodes = [ox.distance.nearest_nodes(graph, point.x, point.y) for point in grid.geometry.centroid]
    return nodes

