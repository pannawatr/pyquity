import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt

def plot_grid(grid, ax=None, linewidth: float=0.5, figsize: tuple[float, float]=(10, 10), legend: bool=True, show: bool=True, **kwargs):
    # Create a new figure and axes if none provided
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    
    # Plot the GeoDataFrame on the axes
    ax = grid.plot(ax=ax, edgecolor='k', color='white', linewidth=linewidth, legend=legend, **kwargs)

    # Display the plot if requested
    if show:
        plt.show()

    return ax

def plot_graph_route_by_mode(G, route, ax=None, show: bool=True, legend: bool=True node_size: float=0, edge_color: str='lightgray'):
    mode_colors = {'walk': 'green', 'transit': 'red', 'bike': 'blue', 'transfer': 'yellow'}

    # Convert the route into a GeoDataFrame (one row per edge) using OSMnx
    gdf = ox.routing.route_to_gdf(G, route)

    # Create a new figure and axes if none provided
    if ax is None:
        fig, ax = ox.plot_graph(G, show=False, close=False, node_size=node_size, edge_color=edge_color)
    
    # Plot each segment of the route, color-coded by its mode
    for mode, data in gdf.groupby('mode'):
        color = mode_colors.get(mode, 'gray')
        data.plot(ax=ax, linewidth=3.5, edgecolor=color, label=mode)

    # Show the legend and plot if requested
    if show:
        plt.show()
    if legend:
        ax.legend()

    return ax