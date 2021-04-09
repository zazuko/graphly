
# -*- coding: utf-8 -*-
from typing import List, Union, TypedDict

import matplotlib
import networkx as nx
import numpy as np
import pandas as pd


def drop_rows_without_duplicate(df: pd.DataFrame, column: str) -> None:
    """ Drop all the rows in dataframe that do not have duplicates.
    The operation is performed in-place.
    Args:
        df          dataframe
        column      column name, for which duplicates are to checked

    Returns:
        None
    """

    all_ids = set(df[column])
    duplicated_ids = set(df[column][df[column].duplicated()])
    ids_to_delete = all_ids.difference(duplicated_ids)

    df.drop(df[df[column].isin(ids_to_delete)].index, inplace=True)
    df = df.reset_index(drop=True)


def matplotlib_to_plotly(cmap: matplotlib.colors.Colormap, pl_entries: int) -> List[Union[int, str]]:
    """ Transform matplotlib colormap to plotly one
    Credits to: https://plotly.com/python/v3/matplotlib-colorscales/

    Args:
                    cmap:           			colormap, matplotlib format
                    pl_entries: 				number of entries in colormap

    Returns:
                    List[Union[int, str]]]      colormap, plotly format
    """

    h = 1.0/(pl_entries-1)
    pl_colorscale = []

    for k in range(pl_entries):
        C = list(map(np.uint8, np.array(cmap(k*h)[:3])*255))
        pl_colorscale.append([k*h, 'rgb'+str((C[0], C[1], C[2]))])

    return pl_colorscale

def get_subgraph(graph: nx.Graph, node: str) -> nx.Graph:
    """Get part of the graph containing certain node. All parts of the original graph that
    are not connected to the node are discared.
    Args:
        graph:          full graph, consisting of many unconnected subgraphs
        node:           node of interest

    Returns:
        nx.Graph:       part of the graph containing node, and all elements connected to the node.
                        Both direct and indirect connections are included.
    """

    relevant_nodes = nx.algorithms.components.node_connected_component(
        graph.to_undirected(), node
    )
    subgraph = graph.subgraph(relevant_nodes)

    return subgraph


class CytoscapeNode(TypedDict):
    id: str


class CytoscapeEdge(TypedDict):
    source: str
    target: str


class CytoscapeElement(TypedDict):

    data: Union[CytoscapeNode, CytoscapeEdge]


def networkx2cytoscape(graph: nx.Graph) -> List[CytoscapeElement]:
    """Transform networkx graph to cytoscape object.
    Args:
        graph:                      a networkx graph

    Returns:
        List[CytoscapeElement]:     a cytoscape graph. Format as per: https://dash.plotly.com/cytoscape/elements
    """

    items = []
    for node in graph.nodes:

        node_properties = graph.nodes[node]
        items.append({"data": {"id": node, **node_properties}})

    for source, target in graph.edges:

        edge_properties = graph.get_edge_data(source, target)
        items.append({"data": {"source": source, "target": target, **edge_properties}})

    return items