import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt

from matplotlib.axes._axes import Axes

def plot_grid(grid: gpd.GeoDataFrame, ax: Axes=None, linewidth: float=0.5, figsize: tuple[float, float]=(8, 8)):
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    ax = grid.plot(ax=ax, edgecolor='k', color='white', linewidth=linewidth, legend=True)
    plt.show()
    return ax
