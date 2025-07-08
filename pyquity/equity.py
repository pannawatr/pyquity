import osmnx as ox
import numpy as np
import networkx as nx
import geopandas as gpd

from .graph import grid_from_place, grid_poi, grid_nearest_node, graph_to_gdf, get_amenity
from .routing import shortest_path
from tqdm import tqdm

def grid_micromobility(grid: gpd.GeoDataFrame, amenity: gpd.GeoDataFrame, micromobility_size: int) -> gpd.GeoDataFrame:
    weight = grid['poi'] / len(amenity)
    weight = weight / weight.sum()
    raw_values = weight * micromobility_size
    grid['micromobility'] = raw_values.apply(np.floor).astype(int)
    remainder = micromobility_size - grid['micromobility'].sum()

    fractional_part = raw_values - np.floor(raw_values)
    indices = fractional_part.sort_values(ascending=False).index[:remainder]
    for index in indices:
        grid.at[index, 'micromobility'] += 1
    return grid

def equity_sufficientarianism(G, grid: gpd.GeoDataFrame, amenity: gpd.GeoDataFrame=None, micromobility_size: int=0):
    if not 'poi' in grid.columns:
        try:
            amenity_type = str(input('You don\'t have amenity in gdf.\nPlease select amenity {"education", "financial", "healthcare"}: '))
            amenity = get_amenity(grid.loc[0].display_name, amenity_type)
        except:
            raise ValueError("")
        grid = grid_poi(grid, amenity)
    
    if not 'micromobility' in grid.columns:
        micromobility_size = int(input('You don\'t have micromobility in gdf.\nPlease input a micromobility size (int): '))
        grid = grid_micromobility(grid, amenity, micromobility_size)
    
    return grid

def equity_egalitarianism():
    return gdf