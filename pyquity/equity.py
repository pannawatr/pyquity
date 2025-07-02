import osmnx as ox
import geopandas as gpd

def grid_micromobility(grid: gpd.GeoDataFrame, amenity: gpd.GeoDataFrame, micromobility_size: int) -> gpd.GeoDataFrame:
    grid['micromobility'] = 0
    for index, x in grid.iterrows():
        weight = x['poi']/len(amenity)
        try:
            grid.at[index, 'micromobility'] = round(weight * micromobility_size)
        except:
            raise ValueError("")
    return grid