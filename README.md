## PyQuity
PyQuity is a compact Python toolkit for building and analyzing multimodal street and transit networks with a focus on accessibility and distributive equity. Quickly generate graphs and grids, attach POIs/GTFS, compute route-based accessibility, and evaluate equity (sufficientarianism, egalitarianism) with seamless GeoPandas/NetworkX integration.

## Installation
PyQuity can be installed via PyPI:
```bash
pip install pyquity
```

## Examples
```python
import pyquity

# Create base graphs
G_walk = pyquity.graph_from_place('Barrie, Canada', network_type='walk')
G_bike = pyquity.graph_from_place('Barrie, Canada', network_type='bike')

# Create GTFS graph (GTFS zip file)
G_gtfs = pyquity.graph_from_gtfs('gtfs.zip')

# Combine base graphs with GTFS graph
MG_walk = pyquity.multimodel_graph(G_walk, G_gtfs)
MG_bike = pyquity.multimodel_graph(G_bike, G_gtfs)
```