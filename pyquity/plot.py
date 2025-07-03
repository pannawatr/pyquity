import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.axes._axes import Axes

from .graph import graph_to_gdf

def plot_grid(grid: gpd.GeoDataFrame, ax: Axes=None, linewidth: float=0.5, figsize: tuple[float, float]=(8, 8)):
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    ax = grid.plot(ax=ax, edgecolor='k', color='white', linewidth=linewidth, legend=True)
    plt.show()
    return ax

def plot_graph(G: gpd.GeoDataFrame or nx.MultiDiGraph or nx.MultiGraph, ax: Axes=None, linewidth: float=0.5, color: str='black', figsize: tuple[float, float]=(8, 8)):
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)

    if G is nx.MultiDiGraph or nx.MultiGraph:
        G = graph_to_gdf(G)
        
    ax = G.plot(ax=ax, markersize=1, linewidth=0.5, color=color)
    plt.show()
    return ax