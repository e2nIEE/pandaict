# -*- coding: utf-8 -*-
"""
Created on Sun Sep 25 11:08:10 2022

@author: janli
"""
import pandaict_orig as pi
import pandaict_orig.plotting as pi_plot

import pandapower as pp
import pandapower.plotting as pp_plot

import pandas as pd
import copy
import networkx as nx
import numpy as np
from itertools import groupby
import test_orig.networks
"""
TOOLBOX
"""

def lists_overlap(List1, List2):
   for i in List1:
       if i in List2:
           return True
   return False

def find_intersection(m_list):
    for i,v in enumerate(m_list) : 
        for j,k in enumerate(m_list[i+1:],i+1):  
           if v & k:
              m_list[i]=v.union(m_list.pop(j))
              return find_intersection(m_list)
    return m_list

def generate_graph_Edges(ict_net):
    Edges = []
    for link in ict_net.link.index:
        fb = ict_net.link.from_node[link]
        tb = ict_net.link.to_node[link]
        Edges.append([fb,tb])
    return Edges

def create_nxgraph(ict_net):
    Edges = generate_graph_Edges(ict_net)
    G = nx.Graph()
    G.add_edges_from(Edges)
    return G

def get_Node_Path(ict_net, Start_Node, End_Node):
    pathes = []
    G = create_nxgraph(ict_net)

    for start_buses in Start_Node:
        for path in nx.all_simple_paths(G, source=start_buses, target=End_Node):
            pathes.append(path)
   
    Node_Path = pathes
    return Node_Path

def get_from_link_to_link(ict_net, Node):
    connected_links = []

    for link in ict_net.link.index:   
        if ict_net.link.from_node[link] == Node:
            connected_links.append(link)
            
        if ict_net.link.to_node[link] == Node:
            connected_links.append(link)
       
    return connected_links

def Get_Line_path_from_node_path(ict_net, Node_Paths):
    link_paths = []
    for path in Node_Paths:
        link_path = []
        for node in range(len(path)-1):
            connected_lines1 = get_from_link_to_link(ict_net, path[node])
            connected_lines2 = get_from_link_to_link(ict_net, path[node+1])
            
            Line = set(connected_lines1).intersection(connected_lines2)
            link_path.append(list(Line)[0])
        link_paths.append(link_path)
        
    return link_paths

def get_connected_links_to_node(ict_net, node):
    links = []
    for line in ict_net.link.index:
        fn = ict_net.link.from_node[line]
        tn = ict_net.link.to_node[line]
    
    if fn == node:
        links.append(line)
    if tn == node:
        links.append(line)
    
    return links

def list_Intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def check_same_contents(nums1, nums2):
  for x in set(nums1 + nums2):
    if nums1.count(x) != nums2.count(x):
      return False
  return True

"""
"""