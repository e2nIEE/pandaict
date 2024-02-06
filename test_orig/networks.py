# -*- coding: utf-8 -*-
"""
Created on Sun Sep 25 10:58:48 2022

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

def ict_Netz_Not_Connected_node():

    ict_net = pi.create_empty_ict_network()

    node1 = pi.create_ict_node(ict_net, name = "Connect_Bus_1", index = 1)
    node2 = pi.create_ict_node(ict_net, name = "Connect_Bus_2,3", index = 2)
    node3 = pi.create_ict_node(ict_net, name = "Connect_Bus_4,5", index = 3)
    node4 = pi.create_ict_node(ict_net, name = "Connect_Bus_6", index = 4)
    node5 = pi.create_ict_node(ict_net, name = "Connect_Bus_7", index = 5)
    
    ict_net.node_geodata.loc[1, ["x", "y"]] = (0, 0)
    ict_net.node_geodata.loc[2, ["x", "y"]] = (2, 0)
    ict_net.node_geodata.loc[3, ["x", "y"]] = (4, 0)
    ict_net.node_geodata.loc[4, ["x", "y"]] = (8, 2)
    ict_net.node_geodata.loc[5, ["x", "y"]] = (8, -2)
    
    protocol1 = ["TCP","5G","3G"]
    
    link1 = pi.create_ict_link(ict_net, node1, node2, protocols=protocol1, length_km=10, type="wired", name="Link_1", index = 1, in_service=True)
    link2 = pi.create_ict_link(ict_net, node2, node3, protocols=protocol1, length_km=0.05, type="wired", name="Link_2", index = 2, in_service=True)
    link3 = pi.create_ict_link(ict_net, node3, node4, protocols=protocol1, length_km=2.0, type="wired", name="Link_3", index = 3, in_service=False)
    # link4 = pi.create_ict_link(ict_net, node3, node5, protocols=protocol1, length_km=2.5, type="wired", name="Link_4", index = 4, in_service=False)
    # link5 = pi.create_ict_link(ict_net, node4, node5, protocols=protocol1, length_km=3.5, type="wired", name="Link_5", index = 5, in_service=True)

    device1 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="ComModul_Node1", index = 1)
    device2 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="Externes_Netz", index = 2)
    device3 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="ComModul_Node2", index = 3)
    device4 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="Bus_Switch_23", index = 4)
    device5 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="HV_Trafo_Com", index = 5)
    device6 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="ComModul_Node3", index = 6)
    device7 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="MV_Trafo_Com", index = 7)
    device8 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Bus_Switch_45", index = 8)
    device9 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_3", index = 9)
    device10 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_8", index = 10)
    device11 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="ComModul_Node4", index = 11)
    device12 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Switch_4", index = 12)
    device13 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Generator", index = 13)
    device14 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Swtich_5", index = 14)
    device15 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="ComModul_Node5", index = 15)
    device16 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_6", index = 16)
    device17 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Static_Generator", index = 17)
    device18 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Load", index = 18)
    device19 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_7", index = 19)
    
    node_c = pi_plot.create_ict_node_collection(ict_net, size = 0.065, color="black")
    link_c = pi_plot.create_ict_link_collection(ict_net, color="black")
    device_c = pi_plot.create_ict_device_collection(ict_net, size = 0.2, color="black")
    
    pp_plot.draw_collections([node_c, link_c, device_c],figsize=(10,8))
    
    return ict_net

def ict_Netz_isolated_node():

    ict_net = pi.create_empty_ict_network()

    node1 = pi.create_ict_node(ict_net, name = "Connect_Bus_1", index = 1)
    node2 = pi.create_ict_node(ict_net, name = "Connect_Bus_2,3", index = 2)
    node3 = pi.create_ict_node(ict_net, name = "Connect_Bus_4,5", index = 3)
    node4 = pi.create_ict_node(ict_net, name = "Connect_Bus_6", index = 4)
    node5 = pi.create_ict_node(ict_net, name = "Connect_Bus_7", index = 5)
    
    ict_net.node_geodata.loc[1, ["x", "y"]] = (0, 0)
    ict_net.node_geodata.loc[2, ["x", "y"]] = (2, 0)
    ict_net.node_geodata.loc[3, ["x", "y"]] = (4, 0)
    ict_net.node_geodata.loc[4, ["x", "y"]] = (8, 2)
    ict_net.node_geodata.loc[5, ["x", "y"]] = (8, -2)
    
    protocol1 = ["TCP","5G","3G"]
    
    link1 = pi.create_ict_link(ict_net, node1, node2, protocols=protocol1, length_km=10, type="wired", name="Link_1", index = 1, in_service=True)
    link2 = pi.create_ict_link(ict_net, node2, node3, protocols=protocol1, length_km=0.05, type="wired", name="Link_2", index = 2, in_service=True)
    link3 = pi.create_ict_link(ict_net, node3, node4, protocols=protocol1, length_km=2.0, type="wired", name="Link_3", index = 3, in_service=False)
    link4 = pi.create_ict_link(ict_net, node3, node5, protocols=protocol1, length_km=2.5, type="wired", name="Link_4", index = 4, in_service=False)
    link5 = pi.create_ict_link(ict_net, node4, node5, protocols=protocol1, length_km=3.5, type="wired", name="Link_5", index = 5, in_service=False)

    device1 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="ComModul_Node1", index = 1)
    device2 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="Externes_Netz", index = 2)
    device3 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="ComModul_Node2", index = 3)
    device4 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="Bus_Switch_23", index = 4)
    device5 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="HV_Trafo_Com", index = 5)
    device6 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="ComModul_Node3", index = 6)
    device7 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="MV_Trafo_Com", index = 7)
    device8 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Bus_Switch_45", index = 8)
    device9 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_3", index = 9)
    device10 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_8", index = 10)
    device11 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="ComModul_Node4", index = 11)
    device12 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Switch_4", index = 12)
    device13 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Generator", index = 13)
    device14 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Swtich_5", index = 14)
    device15 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="ComModul_Node5", index = 15)
    device16 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_6", index = 16)
    device17 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Static_Generator", index = 17)
    device18 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Load", index = 18)
    device19 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_7", index = 19)
    
    node_c = pi_plot.create_ict_node_collection(ict_net, size = 0.065, color="black")
    link_c = pi_plot.create_ict_link_collection(ict_net, color="black")
    device_c = pi_plot.create_ict_device_collection(ict_net, size = 0.2, color="black")
    
    pp_plot.draw_collections([node_c, link_c, device_c],figsize=(10,8))
    
    return ict_net

def ict_Netz_islanded_nodes():

    ict_net = pi.create_empty_ict_network()

    node1 = pi.create_ict_node(ict_net, name = "Connect_Bus_1", index = 1)
    node2 = pi.create_ict_node(ict_net, name = "Connect_Bus_2,3", index = 2)
    node3 = pi.create_ict_node(ict_net, name = "Connect_Bus_4,5", index = 3)
    node4 = pi.create_ict_node(ict_net, name = "Connect_Bus_6", index = 4)
    node5 = pi.create_ict_node(ict_net, name = "Connect_Bus_7", index = 5)
    
    ict_net.node_geodata.loc[1, ["x", "y"]] = (0, 0)
    ict_net.node_geodata.loc[2, ["x", "y"]] = (2, 0)
    ict_net.node_geodata.loc[3, ["x", "y"]] = (4, 0)
    ict_net.node_geodata.loc[4, ["x", "y"]] = (8, 2)
    ict_net.node_geodata.loc[5, ["x", "y"]] = (8, -2)
    
    protocol1 = ["TCP","5G","3G"]
    
    link1 = pi.create_ict_link(ict_net, node1, node2, protocols=protocol1, length_km=10, type="wired", name="Link_1", index = 1, in_service=True)
    link2 = pi.create_ict_link(ict_net, node2, node3, protocols=protocol1, length_km=0.05, type="wired", name="Link_2", index = 2, in_service=True)
    link3 = pi.create_ict_link(ict_net, node3, node4, protocols=protocol1, length_km=2.0, type="wired", name="Link_3", index = 3, in_service=False)
    link4 = pi.create_ict_link(ict_net, node3, node5, protocols=protocol1, length_km=2.5, type="wired", name="Link_4", index = 4, in_service=False)
    link5 = pi.create_ict_link(ict_net, node4, node5, protocols=protocol1, length_km=3.5, type="wired", name="Link_5", index = 5, in_service=True)

    device1 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="ComModul_Node1", index = 1)
    device2 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="Externes_Netz", index = 2)
    device3 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="ComModul_Node2", index = 3)
    device4 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="Bus_Switch_23", index = 4)
    device5 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="HV_Trafo_Com", index = 5)
    device6 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="ComModul_Node3", index = 6)
    device7 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="MV_Trafo_Com", index = 7)
    device8 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Bus_Switch_45", index = 8)
    device9 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_3", index = 9)
    device10 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_8", index = 10)
    device11 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="ComModul_Node4", index = 11)
    device12 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Switch_4", index = 12)
    device13 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Generator", index = 13)
    device14 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Swtich_5", index = 14)
    device15 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="ComModul_Node5", index = 15)
    device16 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_6", index = 16)
    device17 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Static_Generator", index = 17)
    device18 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Load", index = 18)
    device19 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_7", index = 19)
    
    node_c = pi_plot.create_ict_node_collection(ict_net, size = 0.065, color="black")
    link_c = pi_plot.create_ict_link_collection(ict_net, color="black")
    device_c = pi_plot.create_ict_device_collection(ict_net, size = 0.2, color="black")
    
    pp_plot.draw_collections([node_c, link_c, device_c],figsize=(10,8))
    
    return ict_net


def ict_Netz_Path_with_Protocol_nodes_True():

    ict_net = pi.create_empty_ict_network()

    node1 = pi.create_ict_node(ict_net, name = "Connect_Bus_1", index = 1)
    node2 = pi.create_ict_node(ict_net, name = "Connect_Bus_2,3", index = 2)
    node3 = pi.create_ict_node(ict_net, name = "Connect_Bus_4,5", index = 3)
    node4 = pi.create_ict_node(ict_net, name = "Connect_Bus_6", index = 4)
    node5 = pi.create_ict_node(ict_net, name = "Connect_Bus_7", index = 5)
    
    ict_net.node_geodata.loc[1, ["x", "y"]] = (0, 0)
    ict_net.node_geodata.loc[2, ["x", "y"]] = (2, 0)
    ict_net.node_geodata.loc[3, ["x", "y"]] = (4, 0)
    ict_net.node_geodata.loc[4, ["x", "y"]] = (8, 2)
    ict_net.node_geodata.loc[5, ["x", "y"]] = (8, -2)
    
    protocol1 = ["TCP","5G","3G"]
    
    link1 = pi.create_ict_link(ict_net, node1, node2, protocols=protocol1, length_km=10, type="wired", name="Link_1", index = 1, in_service=True)
    link2 = pi.create_ict_link(ict_net, node2, node3, protocols=protocol1, length_km=0.05, type="wired", name="Link_2", index = 2, in_service=True)
    link3 = pi.create_ict_link(ict_net, node3, node4, protocols=protocol1, length_km=2.0, type="wired", name="Link_3", index = 3, in_service=True)
    link4 = pi.create_ict_link(ict_net, node3, node5, protocols=protocol1, length_km=2.5, type="wired", name="Link_4", index = 4, in_service=True)
    link5 = pi.create_ict_link(ict_net, node4, node5, protocols=protocol1, length_km=3.5, type="wired", name="Link_5", index = 5, in_service=True)

    device1 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="ComModul_Node1", index = 1)
    device2 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="Externes_Netz", index = 2)
    device3 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="ComModul_Node2", index = 3)
    device4 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="Bus_Switch_23", index = 4)
    device5 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="HV_Trafo_Com", index = 5)
    device6 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="ComModul_Node3", index = 6)
    device7 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="MV_Trafo_Com", index = 7)
    device8 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Bus_Switch_45", index = 8)
    device9 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_3", index = 9)
    device10 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_8", index = 10)
    device11 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="ComModul_Node4", index = 11)
    device12 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Switch_4", index = 12)
    device13 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Generator", index = 13)
    device14 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Swtich_5", index = 14)
    device15 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="ComModul_Node5", index = 15)
    device16 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_6", index = 16)
    device17 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Static_Generator", index = 17)
    device18 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Load", index = 18)
    device19 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_7", index = 19)
    
    node_c = pi_plot.create_ict_node_collection(ict_net, size = 0.065, color="black")
    link_c = pi_plot.create_ict_link_collection(ict_net, color="black")
    device_c = pi_plot.create_ict_device_collection(ict_net, size = 0.2, color="black")
    
    pp_plot.draw_collections([node_c, link_c, device_c],figsize=(10,8))
    
    return ict_net

def ict_Netz_Path_with_Protocol_nodes_False():

    ict_net = pi.create_empty_ict_network()

    node1 = pi.create_ict_node(ict_net, name = "Connect_Bus_1", index = 1)
    node2 = pi.create_ict_node(ict_net, name = "Connect_Bus_2,3", index = 2)
    node3 = pi.create_ict_node(ict_net, name = "Connect_Bus_4,5", index = 3)
    node4 = pi.create_ict_node(ict_net, name = "Connect_Bus_6", index = 4)
    node5 = pi.create_ict_node(ict_net, name = "Connect_Bus_7", index = 5)
    
    ict_net.node_geodata.loc[1, ["x", "y"]] = (0, 0)
    ict_net.node_geodata.loc[2, ["x", "y"]] = (2, 0)
    ict_net.node_geodata.loc[3, ["x", "y"]] = (4, 0)
    ict_net.node_geodata.loc[4, ["x", "y"]] = (8, 2)
    ict_net.node_geodata.loc[5, ["x", "y"]] = (8, -2)
    
    protocol1 = ["TCP","5G","3G"]
    protocol4 = ["PLC"]
    
    link1 = pi.create_ict_link(ict_net, node1, node2, protocols=protocol1, length_km=10, type="wired", name="Link_1", index = 1, in_service=True)
    link2 = pi.create_ict_link(ict_net, node2, node3, protocols=protocol1, length_km=0.05, type="wired", name="Link_2", index = 2, in_service=True)
    link3 = pi.create_ict_link(ict_net, node3, node4, protocols=protocol1, length_km=2.0, type="wired", name="Link_3", index = 3, in_service=True)
    link4 = pi.create_ict_link(ict_net, node3, node5, protocols=protocol4, length_km=2.5, type="wired", name="Link_4", index = 4, in_service=True)
    link5 = pi.create_ict_link(ict_net, node4, node5, protocols=protocol4, length_km=3.5, type="wired", name="Link_5", index = 5, in_service=True)

    device1 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="ComModul_Node1", index = 1)
    device2 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="Externes_Netz", index = 2)
    device3 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="ComModul_Node2", index = 3)
    device4 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="Bus_Switch_23", index = 4)
    device5 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="HV_Trafo_Com", index = 5)
    device6 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="ComModul_Node3", index = 6)
    device7 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="MV_Trafo_Com", index = 7)
    device8 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Bus_Switch_45", index = 8)
    device9 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_3", index = 9)
    device10 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_8", index = 10)
    device11 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="ComModul_Node4", index = 11)
    device12 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Switch_4", index = 12)
    device13 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Generator", index = 13)
    device14 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Swtich_5", index = 14)
    device15 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="ComModul_Node5", index = 15)
    device16 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_6", index = 16)
    device17 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Static_Generator", index = 17)
    device18 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Load", index = 18)
    device19 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_7", index = 19)
    
    node_c = pi_plot.create_ict_node_collection(ict_net, size = 0.065, color="black")
    link_c = pi_plot.create_ict_link_collection(ict_net, color="black")
    device_c = pi_plot.create_ict_device_collection(ict_net, size = 0.2, color="black")
    
    pp_plot.draw_collections([node_c, link_c, device_c],figsize=(10,8))
    
    return ict_net

def Net_check_Protocol_Conection():

    ict_net = pi.create_empty_ict_network()

    node1 = pi.create_ict_node(ict_net, name = "Connect_Bus_1", index = 1)
    node2 = pi.create_ict_node(ict_net, name = "Connect_Bus_2,3", index = 2)
    node3 = pi.create_ict_node(ict_net, name = "Connect_Bus_4,5", index = 3)
    node4 = pi.create_ict_node(ict_net, name = "Connect_Bus_6", index = 4)
    node5 = pi.create_ict_node(ict_net, name = "Connect_Bus_7", index = 5)
    
    ict_net.node_geodata.loc[1, ["x", "y"]] = (0, 0)
    ict_net.node_geodata.loc[2, ["x", "y"]] = (2, 0)
    ict_net.node_geodata.loc[3, ["x", "y"]] = (4, 0)
    ict_net.node_geodata.loc[4, ["x", "y"]] = (8, 2)
    ict_net.node_geodata.loc[5, ["x", "y"]] = (8, -2)
    
    protocol1 = ["TCP","5G","3G"]
    protocol2 = ["TCP","5G","3G","PLC"]
    
    protocol3 = ["TCP"]
    protocol4 = ["PLC","3G"]
    protocol5 = ["TCP","3G"]
    
    link1 = pi.create_ict_link(ict_net, node1, node2, protocols=protocol1, length_km=10, type="wired", name="Link_1", index = 1, in_service=True)
    link2 = pi.create_ict_link(ict_net, node2, node3, protocols=protocol1, length_km=0.05, type="wired", name="Link_2", index = 2, in_service=True)
    link3 = pi.create_ict_link(ict_net, node3, node4, protocols=protocol1, length_km=2.0, type="wired", name="Link_3", index = 3, in_service=False)
    link4 = pi.create_ict_link(ict_net, node3, node5, protocols=protocol1, length_km=2.5, type="wired", name="Link_4", index = 4, in_service=False)
    link5 = pi.create_ict_link(ict_net, node4, node5, protocols=protocol2, length_km=3.5, type="wired", name="Link_5", index = 5, in_service=True)

    device1 = pi.create_ict_device(ict_net, node1, protocol=protocol3, service=1, interconnects="ComModul_Node1", index = 1)
    device2 = pi.create_ict_device(ict_net, node1, protocol=protocol3, service=1, interconnects="Externes_Netz", index = 2)
    device3 = pi.create_ict_device(ict_net, node2, protocol=protocol3, service=1, interconnects="ComModul_Node2", index = 3)
    device4 = pi.create_ict_device(ict_net, node2, protocol=protocol3, service=1, interconnects="Bus_Switch_23", index = 4)
    device5 = pi.create_ict_device(ict_net, node2, protocol=protocol3, service=1, interconnects="HV_Trafo_Com", index = 5)
    device6 = pi.create_ict_device(ict_net, node3, protocol=protocol3, service=1, interconnects="ComModul_Node3", index = 6)
    device7 = pi.create_ict_device(ict_net, node3, protocol=protocol3, service=1, interconnects="MV_Trafo_Com", index = 7)
    device8 = pi.create_ict_device(ict_net, node3, protocol=protocol3, service=1, interconnects="Bus_Switch_45", index = 8)
    device9 = pi.create_ict_device(ict_net, node3, protocol=protocol3, service=1, interconnects="Line_Switch_3", index = 9)
    device10 = pi.create_ict_device(ict_net, node3, protocol=protocol3, service=1, interconnects="Line_Switch_8", index = 10)
    device11 = pi.create_ict_device(ict_net, node4, protocol=protocol5, service=1, interconnects="ComModul_Node4", index = 11)
    device12 = pi.create_ict_device(ict_net, node4, protocol=protocol5, service=1, interconnects="Line_Switch_4", index = 12)
    device13 = pi.create_ict_device(ict_net, node4, protocol=protocol5, service=1, interconnects="Generator", index = 13)
    device14 = pi.create_ict_device(ict_net, node4, protocol=protocol5, service=1, interconnects="Line_Swtich_5", index = 14)
    device15 = pi.create_ict_device(ict_net, node5, protocol=protocol4, service=1, interconnects="ComModul_Node5", index = 15)
    device16 = pi.create_ict_device(ict_net, node5, protocol=protocol4, service=1, interconnects="Line_Switch_6", index = 16)
    device17 = pi.create_ict_device(ict_net, node5, protocol=protocol4, service=1, interconnects="Static_Generator", index = 17)
    device18 = pi.create_ict_device(ict_net, node5, protocol=protocol4, service=1, interconnects="Load", index = 18)
    device19 = pi.create_ict_device(ict_net, node5, protocol=protocol4, service=1, interconnects="Line_Switch_7", index = 19)
    
    node_c = pi_plot.create_ict_node_collection(ict_net, size = 0.065, color="black")
    link_c = pi_plot.create_ict_link_collection(ict_net, color="black")
    device_c = pi_plot.create_ict_device_collection(ict_net, size = 0.2, color="black")
    
    pp_plot.draw_collections([node_c, link_c, device_c],figsize=(10,8))
    
    return ict_net



def Power_net_ict():

    ict_net = pi.create_empty_ict_network()

    node1 = pi.create_ict_node(ict_net, name = "Connect_Bus_1", index = 1)
    node2 = pi.create_ict_node(ict_net, name = "Connect_Bus_2,3", index = 2)
    node3 = pi.create_ict_node(ict_net, name = "Connect_Bus_4,5", index = 3)
    node4 = pi.create_ict_node(ict_net, name = "Connect_Bus_6", index = 4)
    node5 = pi.create_ict_node(ict_net, name = "Connect_Bus_7", index = 5)
    
    ict_net.node_geodata.loc[1, ["x", "y"]] = (0, 0)
    ict_net.node_geodata.loc[2, ["x", "y"]] = (2, 0)
    ict_net.node_geodata.loc[3, ["x", "y"]] = (4, 0)
    ict_net.node_geodata.loc[4, ["x", "y"]] = (8, 2)
    ict_net.node_geodata.loc[5, ["x", "y"]] = (8, -2)
    
    protocol1 = ["TCP","5G","3G"]
    
    link1 = pi.create_ict_link(ict_net, node1, node2, protocols=protocol1, length_km=10, type="wired", name="Link_1", index = 1, in_service=True)
    link2 = pi.create_ict_link(ict_net, node2, node3, protocols=protocol1, length_km=0.05, type="wired", name="Link_2", index = 2, in_service=True)
    link3 = pi.create_ict_link(ict_net, node3, node4, protocols=protocol1, length_km=2.0, type="wired", name="Link_3", index = 3, in_service=False)
    # link4 = pi.create_ict_link(ict_net, node3, node5, protocols=protocol1, length_km=2.5, type="wired", name="Link_4", index = 4, in_service=False)
    # link5 = pi.create_ict_link(ict_net, node4, node5, protocols=protocol1, length_km=3.5, type="wired", name="Link_5", index = 5, in_service=True)

    device1 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="ComModul_Node1", index = 1)
    device2 = pi.create_ict_device(ict_net, node1, protocol=protocol1, service=1, interconnects="Externes_Netz", index = 2)
    device3 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="ComModul_Node2", index = 3)
    device4 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="Bus_Switch_23", index = 4)
    device5 = pi.create_ict_device(ict_net, node2, protocol=protocol1, service=1, interconnects="HV_Trafo_Com", index = 5)
    device6 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="ComModul_Node3", index = 6)
    device7 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="MV_Trafo_Com", index = 7)
    device8 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Bus_Switch_45", index = 8)
    device9 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_3", index = 9)
    device10 = pi.create_ict_device(ict_net, node3, protocol=protocol1, service=1, interconnects="Line_Switch_8", index = 10)
    device11 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="ComModul_Node4", index = 11)
    device12 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Switch_4", index = 12)
    device13 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Generator", index = 13)
    device14 = pi.create_ict_device(ict_net, node4, protocol=protocol1, service=1, interconnects="Line_Swtich_5", index = 14)
    device15 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="ComModul_Node5", index = 15)
    device16 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_6", index = 16)
    device17 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Static_Generator", index = 17)
    device18 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Load", index = 18)
    device19 = pi.create_ict_device(ict_net, node5, protocol=protocol1, service=1, interconnects="Line_Switch_7", index = 19)
    
    node_c = pi_plot.create_ict_node_collection(ict_net, size = 0.065, color="black")
    link_c = pi_plot.create_ict_link_collection(ict_net, color="black")
    device_c = pi_plot.create_ict_device_collection(ict_net, size = 0.2, color="black")
    
    pp_plot.draw_collections([node_c, link_c, device_c],figsize=(10,8))
    
    return ict_net



def power_Netz():
    
    net = pp.create_empty_network()
    
    bus1 = pp.create_bus(net, name="HV Busbar", vn_kv=110, type="b", index = 1)
    bus2 = pp.create_bus(net, name="HV Busbar 2", vn_kv=110, type="b", index = 2)
    bus3 = pp.create_bus(net, name="HV Transformer Bus", vn_kv=110, type="n", index = 3)
    bus4 = pp.create_bus(net, name="MV Transformer Bus", vn_kv=20, type="n", index = 4)
    bus5 = pp.create_bus(net, name="MV Main Bus", vn_kv=20, type="b", index = 5)
    bus6 = pp.create_bus(net, name="MV Bus 1", vn_kv=20, type="b", index = 6)
    bus7 = pp.create_bus(net, name="MV Bus 2", vn_kv=20, type="b", index = 7)
    
    net.bus_geodata.loc[1, ["x", "y"]] = (0, 0)
    net.bus_geodata.loc[2, ["x", "y"]] = (2, 0)
    net.bus_geodata.loc[3, ["x", "y"]] = (3, 0)
    net.bus_geodata.loc[4, ["x", "y"]] = (4, 0)
    net.bus_geodata.loc[5, ["x", "y"]] = (5, 0)
    net.bus_geodata.loc[6, ["x", "y"]] = (8, 2)
    net.bus_geodata.loc[7, ["x", "y"]] = (8, -2)
    
    pp.create_ext_grid(net, bus1, vm_pu=1.02, va_degree=50)
    
    trafo1 = pp.create_transformer(net, bus3, bus4, name="110kV/20kV transformer", std_type="25 MVA 110/20 kV", index = 1)  

    line1 = pp.create_line(net, bus1, bus2, length_km=10, std_type="N2XS(FL)2Y 1x300 RM/35 64/110 kV",  name="Line 1", index = 1)
    line2 = pp.create_line(net, bus5, bus6, length_km=2.0, std_type="NA2XS2Y 1x240 RM/25 12/20 kV", name="Line 2", index = 2)
    line3 = pp.create_line(net, bus6, bus7, length_km=3.5, std_type="48-AL1/8-ST1A 20.0", name="Line 3", index = 3)
    line4 = pp.create_line(net, bus7, bus5, length_km=2.5, std_type="NA2XS2Y 1x240 RM/25 12/20 kV", name="Line 4", index = 4)
    
    sw1 = pp.create_switch(net, bus2, bus3, et="b", type="CB", closed=True, index = 1)
    sw2 = pp.create_switch(net, bus4, bus5, et="b", type="CB", closed=True, index = 2)
    sw3 = pp.create_switch(net, bus5, line2, et="l", type="LBS", closed=True, index = 3)
    sw4 = pp.create_switch(net, bus6, line2, et="l", type="LBS", closed=True, index = 4)
    sw5 = pp.create_switch(net, bus6, line3, et="l", type="LBS", closed=True, index = 5)
    sw6 = pp.create_switch(net, bus7, line3, et="l", type="LBS", closed=False, index = 6)
    sw7 = pp.create_switch(net, bus7, line4, et="l", type="LBS", closed=True, index = 7)
    sw8 = pp.create_switch(net, bus5, line4, et="l", type="LBS", closed=True, index = 8)    

    load1 = pp.create_load(net, bus7, p_mw=2, q_mvar=4, scaling=0.6, name="load", index = 1)
    load2 = pp.create_load(net, bus7, p_mw=2, q_mvar=4, const_z_percent=30, const_i_percent=20, name="zip_load", index = 2)   

    sgen1 = pp.create_sgen(net, bus7, p_mw=2, q_mvar=-0.5, name="static generator", index = 1)
    
    gen1 = pp.create_gen(net, bus6, p_mw=6, max_q_mvar=3, min_q_mvar=-3, vm_pu=1.03, name="generator", index = 1)

    shunt1 = pp.create_shunt(net, bus3, q_mvar=-0.96, p_mw=0, name='Shunt', index = 1)
    
    pp_plot.simple_plot(net, plot_loads=True, plot_gens=True, plot_sgens=True, plot_line_switches=True)
    
    return net
