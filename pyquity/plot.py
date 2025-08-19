import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

def plot_grid(grid, ax=None, linewidth: float=0.5, figsize: tuple[float, float]=(10, 10), legend: bool=True, show: bool=True, **kwargs):
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    ax = grid.plot(ax=ax, edgecolor='k', color='white', linewidth=linewidth, legend=legend, **kwargs)

    if show:
        plt.show()

    return ax
