'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.07.2025

@author: jringelstein
'''

from   pandaict.utils.enums import NodeType, DeviceType, InfoItem, AppType, RoutingType, SortType
from   pandaict.std_types import create_std_type
from pandaict.topology.ip_address import IP_address
from pandaict.create_empty_net import create_empty_network
from pandaict.create import create_ict_node, create_ict_link, create_ict_device, create_ict_app, create_ict_devapp, create_ict_connection

def create_testnet1():
    ict_net = create_empty_network("Test network 1", True)
    node1 = create_ict_node(ict_net, name="Node1", node_type=NodeType.ROUTER, link_types=["Fiber", "LAN1000"])       
    node2 = create_ict_node(ict_net, name="Node2", node_type=NodeType.ROUTER, link_types=["Fiber", "LAN1000", "ADSL8", "LTE50"])       
    
    (dconv1, aconv1) = create_ict_devapp(ict_net, name="Conv1", device_type=DeviceType.CONVERTER, app_type=AppType.CONVERTER) 
    (dconv2, aconv2) = create_ict_devapp(ict_net, name="Conv2", device_type=DeviceType.CONVERTER, app_type=AppType.CONVERTER) 
    (dconv3, aconv3) = create_ict_devapp(ict_net, name="Conv3", device_type=DeviceType.CONVERTER, app_type=AppType.CONVERTER) 
    
    (dcc, acc) = create_ict_devapp(ict_net, name="CC", device_type=DeviceType.SERVER, app_type=AppType.WEBSERVER) 
    (dpq1, apq1) = create_ict_devapp(ict_net, name="PQ1", device_type=DeviceType.RTU, app_type=AppType.CLIENT)  
    (dpq2, apq2) = create_ict_devapp(ict_net, name="PQ2", device_type=DeviceType.RTU, app_type=AppType.CLIENT)  
    (dsc, asc) = create_ict_devapp(ict_net, name="SC", device_type=DeviceType.RTU, app_type=AppType.CLIENT)      
    (dpc1, apc1) = create_ict_devapp(ict_net, name="PC1", device_type=DeviceType.RTU, app_type=AppType.CLIENT)  
    (dpc2, apc2) = create_ict_devapp(ict_net, name="PC2", device_type=DeviceType.RTU, app_type=AppType.CLIENT)        
                 
    link1 = create_ict_link(ict_net, name="CC_Node1", link_type="LAN1000", from_elt=dcc, to_elt=[node1], length_km=0.01)
    link2 = create_ict_link(ict_net, name="Node1_Node2", link_type="Fiber", from_elt=node1, to_elt=[node2], length_km=25)
    link3 = create_ict_link(ict_net, name="Node2_Conv1", link_type="ADSL8", from_elt=node2, to_elt=[dconv1], length_km=5)
    link4 = create_ict_link(ict_net, name="Node2_Conv2", link_type="LTE50", from_elt=node2, to_elt=[dconv2], length_km=10)        
    link5 = create_ict_link(ict_net, name="Node2_Conv3", link_type="ADSL8", from_elt=node2, to_elt=[dconv3], length_km=5)
    link6 = create_ict_link(ict_net, name="Node2_PQ1", link_type="LAN1000", from_elt=node2, to_elt=[dpq1], length_km=0.01)
    link7 = create_ict_link(ict_net, name="Node2_PQ2", link_type="LAN1000", from_elt=node2, to_elt=[dpq2], length_km=0.01)
    link8 = create_ict_link(ict_net, name="Conv1_PC1", link_type="LAN1000", from_elt=dconv1, to_elt=[dpc1], length_km=0.01)
    link9 = create_ict_link(ict_net, name="Conv2_PC2", link_type="RS485", from_elt=dconv2, to_elt=[dpc2], length_km=0.01)
    link10 = create_ict_link(ict_net, name="Conv3_SC", link_type="Binary", from_elt=dconv3, to_elt=[dsc], length_km=0.001)
    
    conn1 = create_ict_connection(ict_net, name="CC_Conv1", from_app=acc, to_app=aconv1)                   
    conn2 = create_ict_connection(ict_net, name="Conv1_PC1", from_app=aconv1, to_app=apc1)                    
    conn3 = create_ict_connection(ict_net, name="CC_PQ1", from_app=acc, to_app=apq1)                    
    conn4 = create_ict_connection(ict_net, name="CC_Conv2", from_app=acc, to_app=aconv2)                    
    conn5 = create_ict_connection(ict_net, name="Conv2_PC2", from_app=aconv2, to_app=apc2)                    
    conn6 = create_ict_connection(ict_net, name="CC_PQ2", from_app=acc, to_app=apq2)                    
    conn7 = create_ict_connection(ict_net, name="CC_Conv3", from_app=acc, to_app=aconv3)            
    conn8 = create_ict_connection(ict_net, name="Conv3_SC", from_app=aconv3, to_app=asc)
            
    return ict_net        
        
def create_testnet2():
    ict_net2 = create_empty_network("Test network 2", True) 
    node1 = create_ict_node(ict_net2, use_uuid=True, name="Node1", node_type=NodeType.ROUTER, link_types=["Fiber", "LAN1000"]) 
    node2 = create_ict_node(ict_net2, use_uuid=True, name="Node2", node_type=NodeType.ROUTER, link_types=["Fiber", "LAN1000", "ADSL8", "LTE50"]) 
    
    (dconv1, aconv1) = create_ict_devapp(ict_net2, use_uuid=True, name="Conv1", device_type=DeviceType.CONVERTER, app_type=AppType.CONVERTER)    
    (dconv2, aconv2) = create_ict_devapp(ict_net2, use_uuid=True, name="Conv2", device_type=DeviceType.CONVERTER, app_type=AppType.CONVERTER) 
    (dconv3, aconv3) = create_ict_devapp(ict_net2, use_uuid=True, name="Conv3", device_type=DeviceType.CONVERTER, app_type=AppType.CONVERTER) 
    
    (dcc, acc) = create_ict_devapp(ict_net2, use_uuid=True, name="CC", device_type=DeviceType.SERVER, app_type=AppType.WEBSERVER)         
    (dpq1, apq1) = create_ict_devapp(ict_net2, use_uuid=True, name="PQ1", device_type=DeviceType.RTU, app_type=AppType.CLIENT)
    (dpq2, apq2) = create_ict_devapp(ict_net2, use_uuid=True, name="PQ2", device_type=DeviceType.RTU, app_type=AppType.CLIENT)
    (dsc, asc) = create_ict_devapp(ict_net2, use_uuid=True, name="SC", device_type=DeviceType.RTU, app_type=AppType.CLIENT)    
    (dpc1, apc1) = create_ict_devapp(ict_net2, use_uuid=True, name="PC1", device_type=DeviceType.RTU, app_type=AppType.CLIENT)
    (dpc2, apc2) = create_ict_devapp(ict_net2, use_uuid=True, name="PC2", device_type=DeviceType.RTU, app_type=AppType.CLIENT)  
    
    link1 = create_ict_link(ict_net2, use_uuid=True, name="CC_Node1", link_type="LAN1000", from_elt=dcc, to_elt=[node1], length_km=0.01) 
    link2 = create_ict_link(ict_net2, use_uuid=True, name="Node1_Node2", link_type="Fiber", from_elt=node1, to_elt=[node2], length_km=25)
    link3 = create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv1", link_type="ADSL8", from_elt=node2, to_elt=[dconv1], length_km=5)
    link4 = create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv2", link_type="LTE50", from_elt=node2, to_elt=[dconv2], length_km=10)        
    link5 = create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv3", link_type="ADSL8", from_elt=node2, to_elt=[dconv3], length_km=5)
    link6 = create_ict_link(ict_net2, use_uuid=True, name="Node2_PQ1", link_type="LAN1000", from_elt=node2, to_elt=[dpq1], length_km=0.01)
    link7 = create_ict_link(ict_net2, use_uuid=True, name="Node2_PQ2", link_type="LAN1000", from_elt=node2, to_elt=[dpq2], length_km=0.01)
    link8 = create_ict_link(ict_net2, use_uuid=True, name="Conv1_PC1", link_type="LAN1000", from_elt=dconv1, to_elt=[dpc1], length_km=0.01)
    link9 = create_ict_link(ict_net2, use_uuid=True, name="Conv2_PC2", link_type="RS485", from_elt=dconv2, to_elt=[dpc2], length_km=0.01)
    link10 = create_ict_link(ict_net2, use_uuid=True, name="Conv3_SC", link_type="Binary", from_elt=dconv3, to_elt=[dsc], length_km=0.001)
    
    conn1 = create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv1", from_app=acc, to_app=aconv1)                     
    conn2 = create_ict_connection(ict_net2, use_uuid=True, name="Conv1_PC1", from_app=aconv1, to_app=apc1)                     
    conn3 = create_ict_connection(ict_net2, use_uuid=True, name="CC_PQ1", from_app=acc, to_app=apq1)                    
    conn4 = create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv2", from_app=acc, to_app=aconv2)                     
    conn5 = create_ict_connection(ict_net2, use_uuid=True, name="Conv2_PC2", from_app=aconv2, to_app=apc2)                     
    conn6 = create_ict_connection(ict_net2, use_uuid=True, name="CC_PQ2", from_app=acc, to_app=apq2)                    
    conn7 = create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv3", from_app=acc, to_app=aconv3) 
    conn8 = create_ict_connection(ict_net2, use_uuid=True, name="Conv3_SC", from_app=aconv3, to_app=asc) 
    
    return ict_net2

def create_testnet3():
    ict_net3 = create_empty_network("Test network 3", True) 
    
    n1 = create_ict_node(ict_net3, name="N1", node_type=NodeType.ROUTER, link_types=["Fiber", "Fiber", "ADSL8", "LTE50"], mtbf_h=2000, mttr_h=2, ber=0.001)
    n2 = create_ict_node(ict_net3, name="N2", node_type=NodeType.ROUTER, link_types=["LAN1000", "ADSL8", "LTE50"], mtbf_h=1000, mttr_h=1, ber=0.002)
    n3 = create_ict_node(ict_net3, name="N3", node_type=NodeType.ROUTER, link_types=["LAN1000", "Fiber", "ADSL8", "UMTS"], mtbf_h=3000, mttr_h=3, ber=0.003)
    n4 = create_ict_node(ict_net3, name="N4", node_type=NodeType.ROUTER, link_types=["Fiber", "ADSL8", "UMTS", "LTE50"], mtbf_h=2500, mttr_h=1.5, ber=0.004)
    n5 = create_ict_node(ict_net3, name="N5", node_type=NodeType.ROUTER, link_types=["ADSL8", "LTE50"], mtbf_h=1500, mttr_h=2.5, ber=0.005)
    
    d1 = create_ict_device(ict_net3, name="D1", device_type=DeviceType.SERVER)
    a1a = create_ict_app(ict_net3, name="A1a", device=d1, app_type=AppType.CLIENT)
    a1b = create_ict_app(ict_net3, name="A1b", device=d1, app_type=AppType.RESTCLIENT)
    (d2, a2) = create_ict_devapp(ict_net3, name="DA2", device_type=DeviceType.SERVER, app_type=AppType.WEBSERVER)
    (d3, a3) = create_ict_devapp(ict_net3, name="DA3", device_type=DeviceType.SERVER, app_type=AppType.FILESERVER)
    (d4, a4) = create_ict_devapp(ict_net3, name="DA4", device_type=DeviceType.SERVER, app_type=AppType.RESTSERVER)
    
    link1 = create_ict_link(ict_net3, name="D1_N1", link_type="Fiber", from_elt=d1, to_elt=[n1], length_km=1)
    link2 = create_ict_link(ict_net3, name="D2_N2", link_type="LAN1000", from_elt=d2, to_elt=[n2], length_km=1)
    link3 = create_ict_link(ict_net3, name="D3_N3", link_type="LAN1000", from_elt=d3, to_elt=[n3], length_km=1)
    link4 = create_ict_link(ict_net3, name="D4_N4", link_type="Fiber", from_elt=d4, to_elt=[n4], length_km=1)
    link5 = create_ict_link(ict_net3, name="N5_N1", link_type="LTE50", from_elt=n5, to_elt=[n1], length_km=2)
    link6 = create_ict_link(ict_net3, name="N5_N2", link_type="LTE50", from_elt=n5, to_elt=[n2], length_km=2)
    link7 = create_ict_link(ict_net3, name="N3_N5", link_type="ADSL8", from_elt=n3, to_elt=[n5], length_km=3)
    link8 = create_ict_link(ict_net3, name="N5_N4", link_type="ADSL8", from_elt=n5, to_elt=[n4], length_km=4)
    link9 = create_ict_link(ict_net3, name="N2_N1", link_type="ADSL8", from_elt=n2, to_elt=[n1], length_km=3)
    link10 = create_ict_link(ict_net3, name="N1_N3", link_type="Fiber", from_elt=n1, to_elt=[n3], length_km=2)
    link11 = create_ict_link(ict_net3, name="N2_N4", link_type="LTE50", from_elt=n2, to_elt=[n4], length_km=2)
    link12 = create_ict_link(ict_net3, name="N3_N4", link_type="UMTS", from_elt=n3, to_elt=[n4], length_km=0.1)            
    
    return ict_net3
