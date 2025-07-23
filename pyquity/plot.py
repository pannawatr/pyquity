import osmnx as ox
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.axes._axes import Axes

def plot_grid(grid: gpd.GeoDataFrame, ax: Axes=None, linewidth: float=0.5, figsize: tuple[float, float]=(12, 8), **kwargs) -> Axes:
    # If no Axes object is provided, create a new figure and axes with the given size
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Plot the GeoDataFrame on the axes
    ax = grid.plot(ax=ax, edgecolor='k', color='white', linewidth=linewidth, **kwargs)

    # Return the Axes with the plotted grid
    return ax