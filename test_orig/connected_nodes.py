# -*- coding: utf-8 -*-
"""
Created on Sun Jul 24 18:16:28 2022

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
from test_orig.networks import *
from test_orig.toolbox import *

import matplotlib.pyplot as plt
plt.close("all")



# Nicht verbundene Nodes
def get_notconnected_ict_Nodes(ict_net):
    
    notconnected_Node = []
    
    for node in ict_net.node.index:
        if ict_net.link.from_node.isin([node]).any() or ict_net.link.to_node.isin([node]).any():
            pass
        else:
            notconnected_Node.append(node)
   
    notconnected_ict_Nodes = notconnected_Node
    return notconnected_ict_Nodes

# ict_net = ict_Netz_Not_Connected_node()
# notconnected_ict_Nodes = get_notconnected_ict_Nodes(ict_net)
# print("notconnected_ict_Nodes",notconnected_ict_Nodes)




# Isolated Nodes (link nicht in Service) (single)
def get_isolated_ict_Nodes(ict_net):
    
    isolated_Node = []
    link_table = ict_net.link
    
    for node in ict_net.node.index:
        if ict_net.link.from_node.isin([node]).any() or ict_net.link.to_node.isin([node]).any():
            
            connected_links = set(ict_net.link.index[ict_net.link.from_node.isin([node]) | ict_net.link.to_node.isin([node])])
    
            connected_links -= set(link_table[~link_table.in_service].index)

            if len(connected_links) == 0:
                isolated_Node.append(node)
    
    isolated_ict_Nodes = isolated_Node
    
    return isolated_ict_Nodes

# ict_net = ict_Netz_isolated_node()
# isolated_ict_Nodes = get_isolated_ict_Nodes(ict_net)
# print("isolated_ict_Nodes",isolated_ict_Nodes)



# Isolated Nodes (link nicht in Service) (multiple) (Islanding of Nodes)
def get_islanded_collection_ict_Nodes(ict_net):
    
    islanded_Nodes = []
 
    for node in ict_net.node.index:
        connected_Nodes = []
        
        connected_fn_links = set(ict_net.link.index[(ict_net.link.from_node.isin([node])) & ict_net.link.in_service])
        connected_tn_links = set(ict_net.link.index[(ict_net.link.to_node.isin([node])) & ict_net.link.in_service])
        
        if len(connected_tn_links) != 0: 
            connected_Nodes.append(list(set(ict_net.link[ict_net.link.index.isin(connected_tn_links)].from_node)))
            connected_Nodes.append(list(set(ict_net.link[ict_net.link.index.isin(connected_fn_links)].to_node)))
        if len(set([node])) != 0:
            connected_Nodes.append(list(set([node])))
        
        connected_Nodes = np.concatenate((connected_Nodes), axis=None)
        islanded_Nodes.append(connected_Nodes.tolist())
    
    s=[set(i) for i in islanded_Nodes if i]
    
    islanded_ict_Nodes = find_intersection(s)
        
    return islanded_ict_Nodes

# ict_net = ict_Netz_islanded_nodes()
# islanded_ict_Nodes = get_islanded_collection_ict_Nodes(ict_net)
# print("islanded_ict_Nodes",islanded_ict_Nodes)



# Get Connected ComModul Device an Node
def Get_ComModul_Device_on_Node(ict_net, Node, Name_Device = "ComModul"):
    for Device in ict_net.device.index: 
        if ict_net.device.node[Device] == Node:
            if (ict_net.device.interconnects[Device]).find(Name_Device) != -1:
                ComModul_Device = Device 
    
    return ComModul_Device

# ict_net = ict_Netz_islanded_nodes()
# Node = 5
# ComModul_Device = Get_ComModul_Device_on_Node(ict_net, Node)
# print("Node",Node,"ComModul_Device",ComModul_Device)



# Get Paths between 2 nodes with protocol
def Paths_with_protocol(ict_net, Start_Node, End_Node):
   
    Edges = generate_graph_Edges(ict_net)
    G = create_nxgraph(ict_net)
    
    Start_Node_as_List = [Start_Node]
    Node_Paths = get_Node_Path(ict_net, Start_Node = Start_Node_as_List, End_Node = End_Node)

    Line_Paths = Get_Line_path_from_node_path(ict_net, Node_Paths)
        
    Start_Node_Com_Modul = Get_ComModul_Device_on_Node(ict_net, Start_Node, Name_Device = "ComModul")
    End_Node_Com_Modul = Get_ComModul_Device_on_Node(ict_net, End_Node, Name_Device = "ComModul")
    
    Start_Node_Protocols = ict_net.device.protocol[Start_Node_Com_Modul]
    End_Node_Protocols = ict_net.device.protocol[End_Node_Com_Modul]
    
    Usefull_Protocols = list_Intersection(Start_Node_Protocols, End_Node_Protocols)
    
    Usefull_Paths = []
    for Protocol in Usefull_Protocols:
        for path in Line_Paths:
            Path_check = []
            for Line in path:
                Line_Protocol = ict_net.link.protocols[Line]
                
                if Protocol in Line_Protocol and ict_net.link.in_service[Line] == True:
                    Path_check.append(True)
                else:
                    Path_check.append(False)
            
            if all(Path_check):
                Usefull_Paths.append(path)
    
    Usefull_Paths = [list(i) for i in set(map(tuple, Usefull_Paths))]
    
            
    if len(Usefull_Paths) > 0:
        there_is_Path = True
    else:
        there_is_Path = False

    return Usefull_Paths, there_is_Path

# ict_net = ict_Netz_Path_with_Protocol_nodes_True()
# Start_Node = 1
# End_Node = 5
# Possible_Paths, there_is_Path = Paths_with_protocol(ict_net, Start_Node, End_Node)
# print("Paths with Protocol & Service Consider","Possible_Paths",Possible_Paths,"there_is_Path",there_is_Path)
#
# ict_net = ict_Netz_Path_with_Protocol_nodes_False()
# Start_Node = 1
# End_Node = 5
# Possible_Paths, there_is_Path = Paths_with_protocol(ict_net, Start_Node, End_Node)
# print("Paths with Protocol & Service Consider","Possible_Paths",Possible_Paths,"there_is_Path",there_is_Path)


# Returns all possible Communication Pairs
def check_Protocol_Conection(ict_net):

    Nodes_Protocols = []
    for node in ict_net.node.index:
        ComModul = Get_ComModul_Device_on_Node(ict_net, node, Name_Device = "ComModul")
        Protocols = ict_net.device.protocol[ComModul]
        
        Node_ComModul_Protocol = [node,Protocols]
        Nodes_Protocols.append(Node_ComModul_Protocol)
   
    get_protocols = []
    for col1 in Nodes_Protocols:
        for col2 in col1[1]:
            if col2 not in get_protocols:
                get_protocols.append(col2) 
                   
    sort_node_protocols = []
    for proto in get_protocols:
        sort_proto = []
        for col1 in Nodes_Protocols:
            if proto in col1[1]:
                sort_proto.append([proto,col1[0]])
        sort_node_protocols.append(sort_proto)
    
    df_sort_node = pd.DataFrame(columns = ['protocol', 'Node'])
    for protocol in sort_node_protocols: 
        for sub in protocol:   
            # df_sort_node = df_sort_node.append({'protocol': sub[0], 'Node': sub[1]},ignore_index = True)
            df_sort_node.loc[len(df_sort_node)]={'protocol': sub[0], 'Node': sub[1]}

    Node_Islands = get_islanded_collection_ict_Nodes(ict_net)
    
    Communication_connections = []
    for Node_Island in Node_Islands:
        Island_Possible_connections = []
        for Node1 in Node_Island:
            for Node2 in Node_Island:
                if Node1 != Node2:
                    
                    combi = []
                    for subl in Island_Possible_connections:
                        Node_combinationcheck = check_same_contents([Node1,Node2],subl)
                        combi.append(Node_combinationcheck)
                    if not any(combi):
                        Possible_Paths, there_is_Path = Paths_with_protocol(ict_net, Start_Node=Node1, End_Node=Node2)
                        
                        if there_is_Path == True:
                            Island_Possible_connections.append([Node1,Node2])
        
                Communication_connections.append(Island_Possible_connections)
    
    Communication_connections_Combine = [j for i in Communication_connections for j in i]
    Communication_connections = [list(i) for i in set(map(tuple, Communication_connections_Combine))]   
    
    return Communication_connections

# ict_net = Net_check_Protocol_Conection()
# Communication_connections = check_Protocol_Conection(ict_net)
# print("Communication_connections",Communication_connections)


# Plot Net with marked out_of_service links
def Plot_Net_with_link_failure(ict_net, plot_devices = False, node_size = 1, device_size = 1, figsize=(10, 8)):
    
    node_col = pi_plot.create_ict_node_collection(ict_net, nodes=ict_net.node.index, node_geodata=None, size=node_size)
    
    link_out_service = []
    link_in_service = []
    for link in ict_net.link.index:
        if ict_net.link.in_service[link] == False:
            link_out_service.append(link)
        else:
            link_in_service.append(link)
               
    lc_inser = pi_plot.create_ict_link_collection(ict_net, links=link_in_service, use_node_geodata=True, color = "b")     
    lc_outser = pi_plot.create_ict_link_collection(ict_net, links=link_out_service, use_node_geodata=True, color = "r")
    
    if plot_devices == True:
        dc = pi_plot.create_ict_device_collection(ict_net, size=device_size, infofunc=None, orientation=0, picker=False)
        
        pp_plot.draw_collections([node_col, lc_inser, lc_outser, dc], figsize=figsize)
    else:
        pp_plot.draw_collections([node_col, lc_inser, lc_outser], figsize=figsize)
    
    """
    import pandaict.plotting as pi_plot | draw collections ? zz. Pandapower dafür
    """
    
    
ict_net = ict_Netz_islanded_nodes()
plot_devices = False
Plot_Net_with_link_failure(ict_net, plot_devices = True, node_size = 0.05, device_size = 0.25, figsize=(10, 8))
Plot_Net_with_link_failure(ict_net, plot_devices = True, node_size = 0.05, device_size = 0.25, figsize=(10, 8))
plt.show(block=True)






