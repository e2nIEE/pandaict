'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.03.2024

@authors: jringelstein
'''
import unittest
import pandapower as pp
import pandapower.control as control
import pandapower.timeseries as timeseries
from   pandapower.timeseries.data_sources.frame_data import DFData
import pandaict as pi
from   pandaict.utils.utils import uuid2elt, elt2uuid
from   pandaict.utils.enums import NodeType, DeviceType, InfoItem, AppType
from   pandaict.topology.routing import *
import pandas as pd
import math
import csv
import uuid

class Core_Test():
    
    def create_testnet1(self):
        ict_net    = pi.create_empty_network("Test network 1",True)
        node1      = pi.create_ict_node(ict_net, name="Node1", node_type=NodeType.ROUTER, link_types=["Fiber","LAN1000"])       
        node2      = pi.create_ict_node(ict_net, name="Node2", node_type=NodeType.ROUTER, link_types=["Fiber","LAN1000","ADSL8","LTE50"])       
        
        (dconv1, aconv1)      = pi.create_ict_devapp(ict_net, name="Conv1", device_type=pi.DeviceType.CONVERTER, app_type=pi.AppType.CONVERTER) 
        (dconv2, aconv2)      = pi.create_ict_devapp(ict_net, name="Conv2", device_type=pi.DeviceType.CONVERTER, app_type=pi.AppType.CONVERTER) 
        (dconv3, aconv3)      = pi.create_ict_devapp(ict_net, name="Conv3", device_type=pi.DeviceType.CONVERTER, app_type=pi.AppType.CONVERTER) 
        
        (dcc, acc)         = pi.create_ict_devapp(ict_net, name="CC", device_type=pi.DeviceType.SERVER, app_type=pi.AppType.WEBSERVER) 
        (dpq1, apq1)       = pi.create_ict_devapp(ict_net, name="PQ1", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)  
        (dpq2, apq2)       = pi.create_ict_devapp(ict_net, name="PQ2", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)  
        (dsc, asc)         = pi.create_ict_devapp(ict_net, name="SC", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)      
        (dpc1, apc1)       = pi.create_ict_devapp(ict_net, name="PC1", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)  
        (dpc2, apc2)       = pi.create_ict_devapp(ict_net, name="PC2", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)        
                     
        link1      = pi.create_ict_link(ict_net, name="CC_Node1", link_type="LAN1000", from_elt=dcc, to_elt=[node1], length_km=0.01)
        link2      = pi.create_ict_link(ict_net, name="Node1_Node2", link_type="Fiber", from_elt=node1, to_elt=[node2], length_km=25)
        link3      = pi.create_ict_link(ict_net, name="Node2_Conv1", link_type="ADSL8", from_elt=node2, to_elt=[dconv1], length_km=5)
        link4      = pi.create_ict_link(ict_net, name="Node2_Conv2", link_type="LTE50", from_elt=node2, to_elt=[dconv2], length_km=10)        
        link5      = pi.create_ict_link(ict_net, name="Node2_Conv3", link_type="ADSL8", from_elt=node2, to_elt=[dconv3], length_km=5)
        link6      = pi.create_ict_link(ict_net, name="Node2_PQ1", link_type="LAN1000", from_elt=node2, to_elt=[dpq1], length_km=0.01)
        link7      = pi.create_ict_link(ict_net, name="Node2_PQ2", link_type="LAN1000", from_elt=node2, to_elt=[dpq2], length_km=0.01)
        link8      = pi.create_ict_link(ict_net, name="Conv1_PC1", link_type="LAN1000", from_elt=dconv1, to_elt=[dpc1], length_km=0.01)
        link9      = pi.create_ict_link(ict_net, name="Conv2_PC2", link_type="RS485", from_elt=dconv2, to_elt=[dpc2], length_km=0.01)
        link10     = pi.create_ict_link(ict_net, name="Conv3_SC", link_type="Binary", from_elt=dconv3, to_elt=[dsc], length_km=0.001)
        
        conn1      = pi.create_ict_connection(ict_net, name="CC_Conv1", from_app=acc, to_app=aconv1)                   
        conn2      = pi.create_ict_connection(ict_net, name="Conv1_PC1", from_app=aconv1, to_app=apc1)                    
        conn3      = pi.create_ict_connection(ict_net, name="CC_PQ1", from_app=acc, to_app=apq1)                    
        conn4      = pi.create_ict_connection(ict_net, name="CC_Conv2", from_app=acc, to_app=aconv2)                    
        conn5      = pi.create_ict_connection(ict_net, name="Conv2_PC2", from_app=aconv2, to_app=apc2)                    
        conn6      = pi.create_ict_connection(ict_net, name="CC_PQ2", from_app=acc, to_app=apq2)                    
        conn7      = pi.create_ict_connection(ict_net, name="CC_Conv3", from_app=acc, to_app=aconv3)            
        conn8      = pi.create_ict_connection(ict_net, name="Conv3_SC", from_app=aconv3, to_app=asc)
        
        pi.utils.get_links_between(ict_net, node2, dconv2)
        
        return ict_net        
        
    def create_testnet2(self):
        ict_net2   = pi.create_empty_network("Test network 2",True) 
        node1      = pi.create_ict_node(ict_net2, use_uuid=True, name="Node1", node_type=NodeType.ROUTER, link_types=["Fiber","LAN1000"]) 
        node2      = pi.create_ict_node(ict_net2, use_uuid=True, name="Node2", node_type=NodeType.ROUTER, link_types=["Fiber","LAN1000","ADSL8","LTE50"]) 
        
        (dconv1, aconv1) = pi.create_ict_devapp(ict_net2, use_uuid=True, name="Conv1", device_type=pi.DeviceType.CONVERTER, app_type=pi.AppType.CONVERTER)    
        (dconv2, aconv2) = pi.create_ict_devapp(ict_net2, use_uuid=True, name="Conv2", device_type=pi.DeviceType.CONVERTER, app_type=pi.AppType.CONVERTER) 
        (dconv3, aconv3) = pi.create_ict_devapp(ict_net2, use_uuid=True, name="Conv3", device_type=pi.DeviceType.CONVERTER, app_type=pi.AppType.CONVERTER) 
        
        (dcc, acc)   = pi.create_ict_devapp(ict_net2, use_uuid=True, name="CC", device_type=pi.DeviceType.SERVER, app_type=pi.AppType.WEBSERVER)         
        (dpq1, apq1) = pi.create_ict_devapp(ict_net2, use_uuid=True, name="PQ1", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)
        (dpq2, apq2) = pi.create_ict_devapp(ict_net2, use_uuid=True, name="PQ2", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)
        (dsc, asc)   = pi.create_ict_devapp(ict_net2, use_uuid=True, name="SC", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)    
        (dpc1, apc1) = pi.create_ict_devapp(ict_net2, use_uuid=True, name="PC1", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)
        (dpc2, apc2) = pi.create_ict_devapp(ict_net2, use_uuid=True, name="PC2", device_type=pi.DeviceType.RTU, app_type=pi.AppType.CLIENT)  
        
        link1      = pi.create_ict_link(ict_net2, use_uuid=True, name="CC_Node1", link_type="LAN1000", from_elt=dcc, to_elt=[node1], length_km=0.01) 
        link2      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node1_Node2", link_type="Fiber", from_elt=node1, to_elt=[node2], length_km=25)
        link3      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv1", link_type="ADSL8", from_elt=node2, to_elt=[dconv1], length_km=5)
        link4      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv2", link_type="LTE50", from_elt=node2, to_elt=[dconv2], length_km=10)        
        link5      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv3", link_type="ADSL8", from_elt=node2, to_elt=[dconv3], length_km=5)
        link6      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_PQ1", link_type="LAN1000", from_elt=node2, to_elt=[dpq1], length_km=0.01)
        link7      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_PQ2", link_type="LAN1000", from_elt=node2, to_elt=[dpq2], length_km=0.01)
        link8      = pi.create_ict_link(ict_net2, use_uuid=True, name="Conv1_PC1", link_type="LAN1000", from_elt=dconv1, to_elt=[dpc1], length_km=0.01)
        link9      = pi.create_ict_link(ict_net2, use_uuid=True, name="Conv2_PC2", link_type="RS485", from_elt=dconv2, to_elt=[dpc2], length_km=0.01)
        link10     = pi.create_ict_link(ict_net2, use_uuid=True, name="Conv3_SC", link_type="Binary", from_elt=dconv3, to_elt=[dsc], length_km=0.001)
        
        conn1      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv1", from_app=acc, to_app=aconv1)                     
        conn2      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv1_PC1", from_app=aconv1, to_app=apc1)                     
        conn3      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_PQ1", from_app=acc, to_app=apq1)                    
        conn4      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv2", from_app=acc, to_app=aconv2)                     
        conn5      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv2_PC2", from_app=aconv2, to_app=apc2)                     
        conn6      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_PQ2", from_app=acc, to_app=apq2)                    
        conn7      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv3", from_app=acc, to_app=aconv3) 
        conn8      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv3_SC", from_app=aconv3, to_app=asc) 
        
        return ict_net2
    
    def test_create_ict_net(self, utest):        
    
        ict_net = self.create_testnet1()
        ict_net2 = self.create_testnet2()
    
        utest.assertTrue(ict_net.equals_excluding_uuids_and_std_types(ict_net2))   
        return  
    
    def test_save_load(self, utest): 
    
        ict_net = self.create_testnet2()
        pi.to_json(ict_net, 'dummy.json', save_std_types=True)
        ict_net_reloaded = pi.from_json('dummy.json')
    
        utest.assertTrue(ict_net.equals_excluding_uuids_and_std_types(ict_net_reloaded))
        return
    
    def test_inspect_ict_net(self, utest):        
        
        ict_net = self.create_testnet1()                       
        utest.assertTrue(pi.inspect(ict_net))   
        return 
    
    
if __name__ == '__main__':
        
    bt = Core_Test()
               
        
    
     
        
        