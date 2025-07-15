import osmnx as ox
import numpy as np

def gini_index(routes):
    accessibility_score = []
    for route in routes:
        if route == 'inf':
            accessibility_score.append(0)
        else:
            accessibility_score.append(float(1/route))
    
    accessibility_score = np.sort(accessibility_score)
    gini = (np.sum((2 * np.arange(1, len(routes) + 1) - len(routes) - 1) * accessibility_score)) / (len(routes) * np.sum(accessibility_score))
    return gini


def lorenz_curve():
    return lorenz