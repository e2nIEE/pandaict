# -*- coding: utf-8 -*-
"""
Created on 6.03.2024
@author: gbanerjee

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
"""

import networkx as nx
import PIL
import numpy as np
import matplotlib.pyplot as plt



def create_plot(net, draw_type='dev', custom_icons=None):    
    """
    Create a plot.

    :INPUT:
        **net** - The network to be plotted.

        **draw_type** (string) - The type of drawing to be created. There are two possibilities: 'dev' and 'app'. \
            'dev': plotting all devices and nodes as well as links in the ICT grid (physical view) \
            'app': plotting all apps and connections in the ICT grid (logical view).
        
    :OPTIONAL:
        **custom_icons** (dict, default None) - A dictionary of custom icons to be used in the plot. If None, standard icons are used.                              
    
    :OUTPUT:
        **plot** -  The pyplot figure object.                 
              
    :EXAMPLE:
        ::
            
            import networkx as nx
            import matplotlib.pyplot as plt
    
            cicons = {"node": "icons/router.png",
                      "app":  "icons/app.png",
                      "device": "icons/device.png",
                      "converter": "icons/convert.png"}
                
            # Plot the graph for dev
            plot = create_plot(net, draw_type='dev', custom_icons=cicons)
            plot.show()
            
            # Plot the graph for app
            plot = create_plot(net, draw_type='app', custom_icons=cicons)
            plot.show()
        
    """    
    g, edge_labels = __create_g__(custom_icons, draw_type, net)        
            
    ax, fig, pos = __init_networkx__(g, draw_type, edge_labels)

    # Transform from data coordinates (scaled between xlim and ylim) to display coordinates
    tr_figure = ax.transData.transform
    # Transform from display to figure coordinates
    tr_axes = fig.transFigure.inverted().transform

    # Select the size of the image (relative to the X axis)
    icon_size = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.02
    icon_center = icon_size / 2.0

    __draw_labels__(g, icon_center, icon_size, pos, tr_axes, tr_figure)        
    
    # plt.show()        
    return plt.gcf()    
            
        
def __create_g__(custom_icons, draw_type, net):
    icons = __get_icons__(custom_icons)

    # Load images
    images = {}
    for k, fname in icons.items():
        with PIL.Image.open(fname) as imgfile:
            i = np.asarray(imgfile)
            images.update({k: i})            
    
    g = __create_graph__(draw_type, images, net)
        
    # Define colors for 'link' and 'conn' edges
    edge_colors = {'link': 'blue', 'conn': 'green'}
    edge_labels = {}

    __draw_edges__(g, draw_type, edge_colors, edge_labels, net)    
        
    return g, edge_labels


def __draw_labels__(g, icon_center, icon_size, pos, tr_axes, tr_figure):
    # Draw node labels under icons

    for n in g.nodes:
        xf, yf = tr_figure(pos[n])
        xa, ya = tr_axes((xf, yf))
        # get overlapped axes and plot icon
        a = plt.axes([xa - icon_center, ya - icon_center, icon_size, icon_size])
        a.imshow(g.nodes[n]["image"])
        a.axis("off")
        a.text(0.5, -0.1, n, transform=a.transAxes, ha='center', va='top')


def __init_networkx__(g, draw_type, edge_labels):
    # Get a reproducible layout and create figure
    pos = nx.spring_layout(g, seed=1734289230)
    edge_colors = [g[u][v]['color'] for u, v in g.edges()]  # Extract edge colors
    fig, ax = plt.subplots()
    # nx.draw_networkx(g, with_labels=True)
    nx.draw_networkx_edges(
    g,
    pos=pos,
    ax=ax,
    edge_color=edge_colors,
    arrows=True,
    arrowstyle="-",
    min_source_margin=15,
    min_target_margin=15,
    )
    edge_labels = {(u, v): f'{edge_labels.get((u, v), "123")}\n' for u, v in g.edges()}
    nx.draw_networkx_edge_labels(
    g,
    pos=pos,
    edge_labels=edge_labels,
    label_pos=0.5,
    font_size=10,
    font_color='blue' if draw_type == 'dev' else 'green',
    verticalalignment='top',
    horizontalalignment='center',
    ax=ax
    )
    return ax, fig, pos


def __draw_edges__(g, draw_type, edge_colors, edge_labels, net):
    # Iterate over each edge type
    if draw_type == 'dev':
        edge_types = ['link']
    elif draw_type == 'app':
        edge_types = ['conn']
    else:
        raise ValueError(f'{draw_type} not supported')
    for one_edge_type in edge_types:
        # Assign the value of the 'from' attribute to the 'from_fix' attribute for each edge type
        net[one_edge_type]['from_fix'] = net[one_edge_type]['from']
    # Iterate over each edge in the current edge type
    for one_edge in net[one_edge_type].itertuples():
        # Extract source and destination information from the edge
        from_source, from_index = one_edge.from_fix if draw_type != 'app' else ('app', one_edge.from_fix)
        to_source, to_index = one_edge.to[0] if draw_type != 'app' else ('app', one_edge.to)
        

        # Add an edge to the graph, with color based on the edge type
        g.add_edge(net[from_source].loc[from_index, 'name'], net[to_source].loc[to_index, 'name'],
                   color=edge_colors[one_edge_type], label=one_edge.name)
        edge_labels[
            (net[from_source].loc[from_index, 'name'], net[to_source].loc[to_index, 'name'])] = one_edge.name
        edge_labels[
            (net[to_source].loc[to_index, 'name'], net[from_source].loc[from_index, 'name'])] = one_edge.name


def __create_graph__(draw_type, images, net):
    g = nx.Graph()
    if draw_type == 'dev':
        node_types = ['node', 'device']
    elif draw_type == 'app':
        node_types = ['app']
    else:
        raise ValueError(f'{draw_type} not supported')
    for one_node_type in node_types:
        for one_node in net[one_node_type].itertuples():
            # create_node_for this node
            g.add_node(one_node.name, image=images[one_node_type])
    return g


def __get_icons__(custom_icons):
    icons = {}
    if custom_icons is not None:    
        icons = custom_icons
    else:
        import os
        dir_name = os.path.dirname(os.path.abspath(__file__))
        dir_name = os.path.dirname(dir_name)
        dir_name = os.path.dirname(dir_name)
        icons = {
            "node": dir_name + os.sep + "icons" + os.sep + "router.png",
            "app": dir_name + os.sep + "icons" + os.sep + "app.png",
            "device": dir_name + os.sep + "icons" + os.sep + "device.png"            
            }
    return icons
