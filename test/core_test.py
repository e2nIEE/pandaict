'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.03.2024

@authors: jringelstein
'''
import unittest
import pandaict as pi
from   pandaict.utils.utils import uuid2elt, elt2uuid, get_values_for_links
from   pandaict.utils.enums import NodeType, DeviceType, InfoItem, AppType, RoutingType, SortType
from   pandaict.topology.routing import *
from   pandaict.topology.routing import calc_sorted_links_by_connection
from   pandaict.reliability.mtbr_mttf import calc_MTBF_route, calc_MTBF_MTTR_route, calc_MTBF_MTTR_by_lup
from   pandaict.reliability.ber import calc_ber_route, calc_ber_by_lup
from   pandaict.std_types import create_std_type
import pandas as pd
import math
import csv
import uuid
from pandaict.create import create_ict_app
from pandaict.topology.ip_address import IP_address
from pandaict.topology.ip_support import init_extend_network, assign_ipaddr_to_elt, assign_ipaddr_to_elts, set_static_iptable_entry, update_iptables

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
    
    def create_testnet3(self):
        ict_net3   = pi.create_empty_network("Test network 3",True) 
        
        n1      = pi.create_ict_node(ict_net3, name="N1", node_type=NodeType.ROUTER, link_types=["Fiber","Fiber","ADSL8","LTE50"], mtbf_h=2000, mttr_h=2, ber=0.001)
        n2      = pi.create_ict_node(ict_net3, name="N2", node_type=NodeType.ROUTER, link_types=["LAN1000","ADSL8","LTE50"], mtbf_h=1000, mttr_h=1, ber=0.002)
        n3      = pi.create_ict_node(ict_net3, name="N3", node_type=NodeType.ROUTER, link_types=["LAN1000","Fiber","ADSL8","UMTS"], mtbf_h=3000, mttr_h=3, ber=0.003)
        n4      = pi.create_ict_node(ict_net3, name="N4", node_type=NodeType.ROUTER, link_types=["Fiber","ADSL8","UMTS","LTE50"], mtbf_h=2500, mttr_h=1.5, ber=0.004)
        n5      = pi.create_ict_node(ict_net3, name="N5", node_type=NodeType.ROUTER, link_types=["ADSL8","LTE50"], mtbf_h=1500, mttr_h=2.5, ber=0.005)
        
        d1         = pi.create_ict_device(ict_net3, name="D1", device_type=pi.DeviceType.SERVER)
        a1a        = pi.create_ict_app(ict_net3, name="A1a", device=d1, app_type=pi.AppType.CLIENT)
        a1b        = pi.create_ict_app(ict_net3, name="A1b", device=d1, app_type=pi.AppType.RESTCLIENT)
        (d2, a2)   = pi.create_ict_devapp(ict_net3, name="D2", device_type=pi.DeviceType.SERVER, app_type=pi.AppType.WEBSERVER)
        (d3, a3)   = pi.create_ict_devapp(ict_net3, name="D3", device_type=pi.DeviceType.SERVER, app_type=pi.AppType.FILESERVER)
        (d4, a4)   = pi.create_ict_devapp(ict_net3, name="D4", device_type=pi.DeviceType.SERVER, app_type=pi.AppType.RESTSERVER)
        
        link1      = pi.create_ict_link(ict_net3, name="D1_N1", link_type="Fiber", from_elt=d1, to_elt=[n1], length_km=1)
        link2      = pi.create_ict_link(ict_net3, name="D2_N2", link_type="LAN1000", from_elt=d2, to_elt=[n2], length_km=1)
        link3      = pi.create_ict_link(ict_net3, name="D3_N3", link_type="LAN1000", from_elt=d3, to_elt=[n3], length_km=1)
        link4      = pi.create_ict_link(ict_net3, name="D4_N4", link_type="Fiber", from_elt=d4, to_elt=[n4], length_km=1)
        link5      = pi.create_ict_link(ict_net3, name="N5_N1", link_type="LTE50", from_elt=n5, to_elt=[n1], length_km=2)
        link6      = pi.create_ict_link(ict_net3, name="N5_N2", link_type="LTE50", from_elt=n5, to_elt=[n2], length_km=2)
        link7      = pi.create_ict_link(ict_net3, name="N3_N5", link_type="ADSL8", from_elt=n3, to_elt=[n5], length_km=3)
        link8      = pi.create_ict_link(ict_net3, name="N5_N4", link_type="ADSL8", from_elt=n5, to_elt=[n4], length_km=4)
        link9      = pi.create_ict_link(ict_net3, name="N2_N1", link_type="ADSL8", from_elt=n2, to_elt=[n1], length_km=3)
        link10     = pi.create_ict_link(ict_net3, name="N1_N3", link_type="Fiber", from_elt=n1, to_elt=[n3], length_km=2)
        link11     = pi.create_ict_link(ict_net3, name="N2_N4", link_type="LTE50", from_elt=n2, to_elt=[n4], length_km=2)
        link12     = pi.create_ict_link(ict_net3, name="N3_N4", link_type="UMTS", from_elt=n3, to_elt=[n4], length_km=0.1)
        
        conn1      = pi.create_ict_connection(ict_net3, name="D2_D1", from_app=a2, to_app=a1a, protocol="HTTP",
                        info_items=[InfoItem.URL, InfoItem.WEBPAGE], 
                        peers=(a2,a1a), producer=[1,0], prod_freq_ms=[60000, 600])
        conn2      = pi.create_ict_connection(ict_net3, name="D2_D4", from_app=a2, to_app=a4, protocol="HTTP",
                        info_items=[InfoItem.REQUEST, InfoItem.RESPONSE], 
                        peers=(a2,a4), producer=[0,1], prod_freq_ms=[3000, 10])
        conn3      = pi.create_ict_connection(ict_net3, name="D1_D4", from_app=a1b, to_app=a4, protocol="HTTP",
                        info_items=[InfoItem.REQUEST, InfoItem.RESPONSE], 
                        peers=(a1b,a4), producer=[0,1], prod_freq_ms=[3000, 40])
        conn4      = pi.create_ict_connection(ict_net3, name="D3_D4", from_app=a3, to_app=a4, protocol="FTP",
                        info_items=[InfoItem.REQUEST, InfoItem.FILE], 
                        peers=(a3,a4), producer=[1,0], prod_freq_ms=[6000, 20])
        
        return ict_net3
    
    def __assert_node_raises(self, utest, ict_net):
        utest.assertRaises(UserWarning, pi.create_ict_node, ict_net, name="Node1", node_type=AppType.CLIENT)
        utest.assertRaises(UserWarning, pi.create_ict_node, ict_net, name="Node1", node_type=NodeType.ROUTER, geodata={'a':10})
        utest.assertRaises(UserWarning, pi.create_ict_node, ict_net, name="Node1", node_type=NodeType.ROUTER, geodata=10)
        utest.assertRaises(UserWarning, pi.create_ict_node, ict_net, name="Node1", node_type=NodeType.ROUTER, link_types=["Blep","LAN1000"])
        utest.assertRaises(UserWarning, pi.create_ict_node, ict_net, name="Node1", node_type=NodeType.ROUTER, link_types="Mlem")
        
    def __assert_devapp_raises(self, utest, ict_net, dev, app):
        utest.assertRaises(UserWarning, pi.create_ict_device, ict_net=None)
        utest.assertRaises(UserWarning, pi.create_ict_device, ict_net, name="Conv1", index=dev[1])
        utest.assertRaises(UserWarning, pi.create_ict_device, ict_net, device_type=AppType.CLIENT)
        utest.assertRaises(UserWarning, pi.create_ict_app, ict_net=None)       
        utest.assertRaises(UserWarning, pi.create_ict_app, ict_net, name="Conv1", index=app[1])
        utest.assertRaises(UserWarning, pi.create_ict_app, ict_net, app_type=DeviceType.CONVERTER)
        utest.assertRaises(UserWarning, pi.create_ict_app, ict_net, app_type=AppType.CLIENT, device=None)
        utest.assertRaises(UserWarning, pi.create_ict_app, ict_net, app_type=AppType.CLIENT, device=dev, conversions="Mlem")
        utest.assertRaises(UserWarning, pi.create_ict_app, ict_net, app_type=AppType.CLIENT, device=dev, conversions=("TCP", "TCP"))
        utest.assertRaises(UserWarning, pi.create_ict_app, ict_net, app_type=AppType.CLIENT, device=dev, conversions=("TCP", "Mlem")) 
        
    def __assert_link_raises(self, utest, ict_net, elt1, elt2, lnk):
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net=None, from_elt=elt1, to_elt=[elt2])  
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", index=lnk[1], from_elt=elt1, to_elt=[elt2])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", from_elt=None, to_elt=elt2)
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", from_elt="Mlem", to_elt=elt2)
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", from_elt=elt1, to_elt=[None])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", from_elt=elt1, to_elt=1)
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", from_elt=elt1, to_elt=["Mlem"])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", from_elt=elt1, to_elt=[("Mlem",1)])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", from_elt=lnk, to_elt=elt2)
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", from_elt=elt2, to_elt=lnk)
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", link_type="Blep", from_elt=elt1, to_elt=[elt2])    
        
    def __assert_conn_raises(self, utest, ict_net, app1, app2, lnk, con):
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net=None)          
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=None, to_app=app1)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=None)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=1, to_app=app1)    
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=[app1])
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app="Blep")
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, peers=("Mlem", "Blep"))
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, peers=10)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, peers=(1,2))
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, peers=(app1,lnk))
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, peers=(app1,app1))
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, protocol="Mlem")
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, protocol=["TCP", "Blep"])                 
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, info_items=10)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, info_items=[InfoItem.ACK, AppType.CLIENT])
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, producer=10)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, info_items=[InfoItem.ACK, InfoItem.FILE], producer=[1,0.3])
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, info_items=[InfoItem.ACK, InfoItem.FILE], producer=[1])
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, info_items=[InfoItem.ACK, InfoItem.FILE], prod_freq_ms=10)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, info_items=[InfoItem.ACK, InfoItem.FILE], prod_freq_ms=[10])
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, info_items=[InfoItem.ACK, InfoItem.FILE], prod_freq_ms=["Mlem", "Blep"])                
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", from_app=app1, to_app=app2, index=con[1])
        
    
    def __test_user_input_checks_nouuid(self, utest):
        
        ict_net    = pi.create_empty_network("Test network 1",True)    
           
        node1            = pi.create_ict_node(ict_net, name="Node1", node_type=NodeType.ROUTER, link_types=["Fiber","LAN1000"])       
        node2            = pi.create_ict_node(ict_net, name="Node2", node_type=NodeType.ROUTER, link_types=["Fiber","LAN1000","ADSL8","LTE50"])               
        (dconv1, aconv1) = pi.create_ict_devapp(ict_net, name="Conv1", device_type=DeviceType.CONVERTER, app_type=AppType.CONVERTER)                                        
        (dcc, acc)       = pi.create_ict_devapp(ict_net, name="CC", device_type=DeviceType.SERVER, app_type=AppType.WEBSERVER) 
        (dsc, asc)       = pi.create_ict_devapp(ict_net, name="SC", device_type=DeviceType.RTU, app_type=AppType.CLIENT)                      
        link1            = pi.create_ict_link(ict_net, name="CC_Node1", link_type="LAN1000", from_elt=dcc, to_elt=[node1], length_km=0.01)                                                                
        conn1            = pi.create_ict_connection(ict_net, name="CC_Conv1", from_app=acc, to_app=asc)
                        
        self.__assert_node_raises(utest, ict_net)
        self.__assert_devapp_raises(utest, ict_net, dconv1, aconv1)
        self.__assert_link_raises(utest, ict_net, dcc, node1, link1)
        self.__assert_conn_raises(utest, ict_net, acc, asc, link1, conn1)
                    
    def __test_user_input_checks_uuid(self, utest):
        ict_net          = pi.create_empty_network("Test network 1",True)   
        node1            = pi.create_ict_node(ict_net, name="Node1", node_type=NodeType.ROUTER, link_types=["Fiber","LAN1000"], use_uuid=True)       
        node2            = pi.create_ict_node(ict_net, name="Node2", node_type=NodeType.ROUTER, link_types=["Fiber","LAN1000","ADSL8","LTE50"])
        (dconv1, aconv1) = pi.create_ict_devapp(ict_net, name="Conv1", use_uuid=True, device_type=DeviceType.CONVERTER, app_type=AppType.CONVERTER)            
        (dcc, acc)       = pi.create_ict_devapp(ict_net, name="CC", use_uuid=True, device_type=DeviceType.SERVER, app_type=AppType.WEBSERVER) 
        (dsc, asc)       = pi.create_ict_devapp(ict_net, name="SC", use_uuid=True, device_type=DeviceType.RTU, app_type=AppType.CLIENT)              
        link1            = pi.create_ict_link(ict_net, name="CC_Node1", use_uuid=True, link_type="LAN1000", from_elt=dcc, to_elt=[node1], length_km=0.01)
        conn1            = pi.create_ict_connection(ict_net, name="CC_Conv1", use_uuid=True, from_app=acc, to_app=asc)
        
        utest.assertRaises(UserWarning, pi.create_ict_node, ict_net, name="Node1", node_type=NodeType.ROUTER, use_uuid=True, uid=10)
        utest.assertRaises(UserWarning, pi.create_ict_node, ict_net, name="Node1", node_type=NodeType.ROUTER, use_uuid=True, uid="Bleeeh")        
        utest.assertRaises(UserWarning, pi.create_ict_node, ict_net, name="Node1", node_type=NodeType.ROUTER, use_uuid=True, uid=node1)                            
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", use_uuid=True, from_elt=('device',0), to_elt=[node1])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", use_uuid=True, uid=dcc, from_elt=10, to_elt=[node1])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", use_uuid=True, uid=dcc, from_elt=dcc, to_elt=[node1])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", use_uuid=True, uid=dcc, from_elt=dcc, to_elt=["Blep"])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", use_uuid=True, uid=node1, from_elt=dcc, to_elt=node1)
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", use_uuid=True, uid=node1, from_elt=dcc, to_elt=[node1])
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", use_uuid=True, from_elt=acc, to_elt=node1)
        utest.assertRaises(UserWarning, pi.create_ict_link, ict_net, name="CC_Node1", use_uuid=True, from_elt=dcc, to_elt=acc)                
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, from_app=10, to_app=asc)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, from_app=acc, to_app=10)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, from_app=acc, to_app=acc)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, uid=acc, from_app=acc, to_app=asc)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, uid=asc, from_app=acc, to_app=asc)
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, from_app=acc, to_app=asc, peers=(acc, 10))
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, from_app=acc, to_app=asc, peers=(10, asc))        
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, from_app=acc, to_app=asc, peers=(link1, acc))
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, from_app=acc, to_app=asc, peers=(acc, link1))
        utest.assertRaises(UserWarning, pi.create_ict_connection, ict_net, name="CC_Conv1", use_uuid=True, from_app=acc, to_app=asc, peers=(acc, acc))
        
    def test_create_ict_net(self, utest):        
    
        ict_net  = self.create_testnet1()
        ict_net2 = self.create_testnet2()
    
        utest.assertTrue(ict_net.equals_excluding_uuids(ict_net2))   
        return  
    
    def test_save_load(self, utest, ict_net=None): 
    
        if ict_net is None: 
            ict_net = self.create_testnet2()
        pi.to_json(ict_net, 'dummy.json', save_std_types=True)
        ict_net_reloaded = pi.from_json('dummy.json')
    
        utest.assertTrue(ict_net.equals_excluding_uuids(ict_net_reloaded, include_std_types=True))
        return
    
    def test_inspect_ict_net(self, utest):        
        
        ict_net = self.create_testnet1()                       
        utest.assertTrue(pi.inspect(ict_net))   
        return 
    
    def test_user_input_checks(self, utest):        
        self.__test_user_input_checks_nouuid(utest)
        self.__test_user_input_checks_uuid(utest)                     
        return 
    
    def test_lup_table_calc(self, utest):
    
        ict_net = self.create_testnet3()
        link_bw = {}
        for i, _ in ict_net['conn'].iterrows():
            # TODO: what if connection is not at all possible? 
            lup_table = calc_lup_table(ict_net, ('conn', i), RoutingType.LOWEST_TOTAL_LATENCY, respect_iptables=False)
            link_bw = add_link_bandwidth_Mbps(ict_net, link_bw, lup_table)
        
        link_bw_cmp = {1: [0.8854053333333334, 11.4694144], 8: [0.8738, 0.0006144], 0: [0.012219733333333333, 3.741], 10: [0.011605333333333334, 11.4688], 3: [14.341802666666666, 26.258810666666665], 4: [2.8672, 0.011605333333333334], 7: [0.011605333333333334, 2.8672], 2: [26.235599999999998, 0.005802666666666667], 11: [26.235599999999998, 0.005802666666666667]}
        # Note: there are links unused (5,6,9) but that may be OK - hard to tell, though
        # TODO: add method that checks if there are overloaded links (look at link 11 here!)

        utest.assertEqual(link_bw, link_bw_cmp)
            
        return
    
    def test_sorted_link_calc(self, utest):
    
        ict_net = self.create_testnet3()
        link_bw = {}
        
        # testing value fetching
        values, vtype = get_values_for_links(ict_net, [('link',3),('link',4),('link',5),('link',6),('link',10)], 'ber')
        utest.assertEqual(values, [0.0001, 0.001, 0.001, 0.0015, 0.001])
        utest.assertEqual(vtype, 'bit_error_rate')
        values, vtype = get_values_for_links(ict_net, [('link',0),('link',2),('link',8),('link',9)], 'bandwidth')
        utest.assertEqual(values, [(1000, 1000), (1000, 1000), (8, 1), (1000, 1000)])
        utest.assertEqual(vtype, 'bandwidth_Mbps')
        values, vtype = get_values_for_links(ict_net, [('link',1),('link',7),('link',9),('link',11)], 'latency')
        utest.assertEqual(values, [100, (200, 300), 100, (300, 300)])
        utest.assertEqual(vtype, 'latency_ms')
        values, vtype = get_values_for_links(ict_net, ('link',10), 'bandwidth')
        utest.assertEqual(values, [(50, 10)])
        utest.assertEqual(vtype, 'bandwidth_Mbps')
        
        # testing sorted link fetching
        down_links, up_links = calc_sorted_links_by_connection(ict_net, ('conn',0))
        utest.assertEqual(down_links, [{'route': 0, 'probability': 1.0, 'links': [{'link': 1, 'downstream': True}, {'link': 0, 'downstream': False}, {'link': 8, 'downstream': True}], 
                                         'values': [100, 100, 200], 'valuetype': 'latency_ms'}])
        utest.assertEqual(up_links, [{'route': 1, 'probability': 1.0, 'links': [{'link': 0, 'downstream': True}, {'link': 1, 'downstream': False}, {'link': 8, 'downstream': False}], 
                                       'values': [100, 100, 300], 'valuetype': 'latency_ms'}])
        down_links, up_links = calc_sorted_links_by_connection(ict_net, ('conn',1))
        utest.assertEqual(down_links, [{'route': 0, 'probability': 1.0, 'links': [{'link': 1, 'downstream': True}, {'link': 10, 'downstream': True}, {'link': 3, 'downstream': False}], 
                                         'values': [100, 100, 100], 'valuetype': 'latency_ms'}])
        utest.assertEqual(up_links, [{'route': 1, 'probability': 1.0, 'links': [{'link': 3, 'downstream': True}, {'link': 1, 'downstream': False}, {'link': 10, 'downstream': False}], 
                                       'values': [100, 100, 200], 'valuetype': 'latency_ms'}])
        down_links, up_links = calc_sorted_links_by_connection(ict_net, ('conn',2))
        utest.assertEqual(down_links, [{'route': 0, 'probability': 1.0, 'links': [{'link': 0, 'downstream': True}, {'link': 3, 'downstream': False}, {'link': 4, 'downstream': False}, {'link': 7, 'downstream': True}], 
                                         'values': [100, 100, 200, 200], 'valuetype': 'latency_ms'}])
        utest.assertEqual(up_links, [{'route': 1, 'probability': 1.0, 'links': [{'link': 3, 'downstream': True}, {'link': 4, 'downstream': True}, {'link': 0, 'downstream': False}, {'link': 7, 'downstream': False}], 
                                       'values': [100, 100, 100, 300], 'valuetype': 'latency_ms'}])
        down_links, up_links = calc_sorted_links_by_connection(ict_net, ('conn',3))
        utest.assertEqual(down_links, [{'route': 0, 'probability': 1.0, 'links': [{'link': 2, 'downstream': True}, {'link': 3, 'downstream': False}, {'link': 11, 'downstream': True}], 
                                         'values': [100, 100, 300], 'valuetype': 'latency_ms'}])
        utest.assertEqual(up_links, [{'route': 1, 'probability': 1.0, 'links': [{'link': 3, 'downstream': True}, {'link': 2, 'downstream': False}, {'link': 11, 'downstream': False}], 
                                       'values': [100, 100, 300], 'valuetype': 'latency_ms'}])

            
        return

    def test_calc_conn_vol_MB(self, utest):
        ict_net = self.create_testnet3()
        res_exp = calc_conn_vol_MB(ict_net, ("app", "D2"), 86400)
        expected_res = {'D2 A1a': {'down': 9437.04, 'up': 6.63552},
                        'D2 D4': {'down': 125.33760000000001, 'up': 123863.04},
                        'tot_dv_down': 9562.377600000002,
                        'tot_dv_up': 123869.67551999999}
        utest.assertEqual(res_exp, expected_res)

        res_cal = calc_conn_vol_MB(ict_net, ("app", "D4"), 86400)
        calculated_res = {'D2 D4': {'down': 125.33760000000001, 'up': 123863.04},
                          'A1b D4': {'down': 125.33760000000001, 'up': 30965.76},
                          'D3 D4': {'down': 283344.48, 'up': 62.668800000000005},
                          'tot_dv_down': 283595.1552, 'tot_dv_up': 154891.4688}
        utest.assertEqual(res_cal, calculated_res)

        return
        
    def test_mtbf_mttr_ber_calc(self, utest):  
        ict_net = self.create_testnet3()
        
        # single route testing
        ber_d = []
        ber_u = []
        for i, _ in ict_net['conn'].iterrows():
            lup_table = calc_lup_table(ict_net, ('conn', i), RoutingType.LOWEST_TOTAL_LATENCY)            
            
            # downstream direction
            links_d = [('link', l['link']) for l in lup_table.get_route(0)['links']]
            (MTBF_d, MTTR_d) = calc_MTBF_MTTR_route(ict_net, links_d)
            MTBF_d2 = calc_MTBF_route(ict_net, links_d)                
            # upstream direction
            links_u = [('link', l['link']) for l in lup_table.get_route(1)['links']]
            (MTBF_u, MTTR_u) = calc_MTBF_MTTR_route(ict_net, links_u)
            MTBF_u2 = calc_MTBF_route(ict_net, links_u)                                        
            
            utest.assertAlmostEqual(MTBF_d, MTBF_d2, delta=0.00001) # MTBF calculated by different methods must be equal
            utest.assertAlmostEqual(MTBF_u, MTBF_u2, delta=0.00001)
            if (set(links_u)==set(links_d)):
                utest.assertAlmostEqual(MTBF_d, MTBF_u, delta=0.00001)  # MTTR for down- and upstream must be equal
                utest.assertAlmostEqual(MTBF_d2, MTBF_u2, delta=0.00001)  # MTTR for down- and upstream must be equal
                utest.assertAlmostEqual(MTTR_d, MTTR_u, delta=0.00001)  # MTTR for down- and upstream must be equal

            ber_d += [calc_ber_route(ict_net, links_d)]
            ber_u += [calc_ber_route(ict_net, links_u)]
            
        expected_ber_d = [0.005091, 0.007582, 0.013137, 0.007633]
        expected_ber_u = [0.005091, 0.007581, 0.009665, 0.007633]
        utest.assertEqual(len(expected_ber_d), len(ber_d))
        for i in range(0, len(expected_ber_d)):
            utest.assertAlmostEqual(expected_ber_d[i], ber_d[i], delta=0.00001)
            utest.assertAlmostEqual(expected_ber_u[i], ber_u[i], delta=0.00001)
                 
        # connection level testing
        expected_MTBF = [74.074, 119.048, 53.860, 78.534]
        expected_MTTR = [1.704, 2.095, 2.061, 1.775]
        expected_ber = [0.005091, 0.007582, 0.013137, 0.007633]
        calculated_MTBF = []
        calculated_MTTR = []
        calculated_ber = []
        for i, _ in ict_net['conn'].iterrows():
            lup_table = calc_lup_table(ict_net, ('conn', i), RoutingType.LOWEST_TOTAL_LATENCY) 
            (MTBF_conn, MTTR_conn) = calc_MTBF_MTTR_by_lup(ict_net, lup_table, downstream=True)
            ber_conn = calc_ber_by_lup(ict_net, lup_table, downstream=True)                        
            calculated_MTBF += [MTBF_conn]
            calculated_MTTR += [MTTR_conn]
            calculated_ber += [ber_conn]
        
        utest.assertEqual(len(expected_MTBF), len(calculated_MTBF))
        for i in range(0,len(expected_MTBF)):
            utest.assertAlmostEqual(expected_MTBF[i], calculated_MTBF[i], delta=0.001)
            utest.assertAlmostEqual(expected_MTTR[i], calculated_MTTR[i], delta=0.001)
            utest.assertAlmostEqual(expected_ber[i], calculated_ber[i], delta=0.001)
        return 
    
    
    def __get_custom_link_protocol_types(self):
        custom_link = { # 10BASE2 unidirectional (not too realistic, just for testing)
            "bandwidth_Mbps": 10,
            "latency_ms": 300,
            "wired": True,
            "protocols": ['TCP','UDP','FTP','HTTP','HTTPS','MODBUS-TCP', 'SFTP'],
            "ber_per_km": 0.001,
            "mtbf_h": 500,
            "mttr_h": 1,
            "uuid": uuid.uuid4()     
        }
        
        custom_protocol = { # SFTP       
            "base_package_size_byte": 500,
            "info_items":
                [ InfoItem.REQUEST,
                  InfoItem.RESPONSE,
                  InfoItem.CERTIFICATE,
                  InfoItem.FILE,                                    
                ], 
            "uuid": uuid.uuid4()      
        }
        
        return custom_link, custom_protocol
    
    def __create_testnet3mod_with_custom_types(self):
        
        ict_net = self.create_testnet3()
        
        custom_link, custom_protocol = self.__get_custom_link_protocol_types()
        create_std_type(ict_net, custom_link, "10BASE2_oneway", element="link")
        create_std_type(ict_net, custom_protocol, "SFTP", element="protocol")
        
        ict_net.link.at[4,"type"] = "10BASE2_oneway"
        ict_net.link.at[9,"type"] = "10BASE2_oneway"
        ict_net.link.at[11,"type"] = "10BASE2_oneway"        
        ict_net.node.at[0,"link_types"] += ["10BASE2_oneway"]
        ict_net.node.at[1,"link_types"] += ["10BASE2_oneway"]
        ict_net.node.at[2,"link_types"] += ["10BASE2_oneway"]
        ict_net.conn.at[2,"protocol"] = "TCP"
    
        return ict_net, custom_link, custom_protocol
    
    def test_custom_type_creation(self, utest):
        
        ict_net, custom_link, custom_protocol = self.__create_testnet3mod_with_custom_types()            
        
        utest.assertEqual(ict_net.std_types['link']['10BASE2_oneway'],  custom_link)
        utest.assertEqual(ict_net.std_types['protocol']['SFTP'],  custom_protocol)
        
        # test save/load
        pi.to_json(ict_net, 'dummy.json', save_std_types=True)
        ict_net_reloaded = pi.from_json('dummy.json')    
        utest.assertTrue(ict_net.equals_excluding_uuids(ict_net_reloaded, include_std_types=True))
        
        # test path calculation for conn 2
        proutes = calc_routes_for_connection(ict_net, ('conn',2), verbose=False)
        utest.assertEqual(proutes, [{'direction': 'downstream', 'path': [('device', 0), ('node', 0), ('node', 1), ('node', 4), ('node', 2), ('node', 3), ('device', 3)]}, 
                                    {'direction': 'bidirectional', 'path': [('device', 0), ('node', 0), ('node', 1), ('node', 4), ('node', 3), ('device', 3)]}, 
                                    {'direction': 'bidirectional', 'path': [('device', 0), ('node', 0), ('node', 1), ('node', 3), ('device', 3)]}, 
                                    {'direction': 'downstream', 'path': [('device', 0), ('node', 0), ('node', 2), ('node', 4), ('node', 1), ('node', 3), ('device', 3)]}, 
                                    {'direction': 'downstream', 'path': [('device', 0), ('node', 0), ('node', 2), ('node', 4), ('node', 3), ('device', 3)]}, 
                                    {'direction': 'downstream', 'path': [('device', 0), ('node', 0), ('node', 2), ('node', 3), ('device', 3)]}, 
                                    {'direction': 'upstream', 'path': [('device', 3), ('node', 3), ('node', 4), ('node', 0), ('device', 0)]}, 
                                    {'direction': 'upstream', 'path': [('device', 3), ('node', 3), ('node', 1), ('node', 4), ('node', 0), ('device', 0)]}])
        return
    
    def test_is_connection_possible(self, utest):
        ict_net, _, _ = self.__create_testnet3mod_with_custom_types()  
        
        # Remove central node and direct bidir link between N2-N4
        ict_net.node.at[4,'in_service']  = False
        ict_net.link.at[10,'in_service'] = False
        
        (down1, up1) = is_connection_possible(ict_net, ('conn',0)) 
        (down2, up2) = is_connection_possible(ict_net, ('conn',1)) 
        (down3, up3) = is_connection_possible(ict_net, ('conn',2)) 
        (down4, up4) = is_connection_possible(ict_net, ('conn',3))
        
        utest.assertTrue( (down1, up1)==(True,True) and (down2, up2)==(True,False) and (down3, up3)==(True,False) and (down4, up4)==(True,False) ) 
        
        return 
    
    def test_ip_support(self, utest):    
        # TODO: add test for assign_ipaddr_to_elts, last_hostIP_in_network, ip.inc
                            
        ict_net = self.create_testnet3()
        init_extend_network(ict_net)
        assign_ipaddr_to_elt(ict_net, ('device',0), ip="192.168.1.1/24")
        assign_ipaddr_to_elt(ict_net, ('device',1), ip="192.168.2.1/24")
        assign_ipaddr_to_elt(ict_net, ('device',2), ip="192.168.3.1/24")
        assign_ipaddr_to_elt(ict_net, ('device',3), ip="192.168.4.1/24")
        assign_ipaddr_to_elt(ict_net, ('node',0), ip=["192.168.1.0/24", "10.1.1.0/20", "10.2.1.0/20", "10.0.1.0/20"])
        assign_ipaddr_to_elt(ict_net, ('node',1), ip=["192.168.2.0/24", "10.2.2.0/20", "10.0.2.0/20"])
        assign_ipaddr_to_elt(ict_net, ('node',2), ip=["192.168.3.0/24", "10.1.3.0/20", "10.2.3.0/20", "10.4.3.0/20"])
        assign_ipaddr_to_elt(ict_net, ('node',3), ip=["192.168.4.0/24", "10.2.4.0/20", "10.4.4.0/20", "10.0.4.0/20"])
        assign_ipaddr_to_elt(ict_net, ('node',4), ip=["10.2.5.0/20", "10.0.5.0/20"])            

        set_static_iptable_entry(ict_net, ('node',0), "192.168.4.1", "10.1.3.0", link_idx=1, metric=10)
        set_static_iptable_entry(ict_net, ('node',2), "192.168.4.1", "10.4.4.0", metric=10)    
        lup_table0 = calc_lup_table(ict_net, ('conn', 0), RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True) 
        update_iptables(ict_net, lup_table0)
        lup_table1 = calc_lup_table(ict_net, ('conn', 1), RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True) 
        update_iptables(ict_net, lup_table1)
        lup_table2 = calc_lup_table(ict_net, ('conn', 2), RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True) 
        update_iptables(ict_net, lup_table2)
        lup_table3 = calc_lup_table(ict_net, ('conn', 3), RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True) 
        update_iptables(ict_net, lup_table3)
        
        expected = {'node_idx': {0: 0, 1: 2, 2: 1, 3: 0, 4: 0, 5: 1, 6: 1, 7: 3, 8: 3, 9: 3, 10: 3, 11: 2}, 
                    'entry': {0: 0, 1: 0, 2: 0, 3: 1, 4: 2, 5: 1, 6: 2, 7: 0, 8: 1, 9: 2, 10: 3, 11: 1}, 
                    'destination': {0: '192.168.4.1', 1: '192.168.4.1', 2: '192.168.1.1', 3: '192.168.1.1', 4: '192.168.2.1', 
                                    5: '192.168.2.1', 6: '192.168.4.1', 7: '192.168.4.1', 8: '192.168.2.1', 9: '192.168.1.1', 
                                    10: '192.168.3.1', 11: '192.168.3.1'}, 
                    'netmask': {0: '255.255.240.0', 1: '255.255.240.0', 2: '255.255.240.0', 3: '255.255.255.0', 4: '255.255.240.0', 
                                5: '255.255.255.0', 6: '255.255.240.0', 7: '255.255.255.0', 8: '255.255.240.0', 9: '255.255.240.0', 
                                10: '255.255.240.0', 11: '255.255.255.0'}, 
                    'gateway': {0: '10.1.3.0', 1: '10.4.4.0', 2: '10.2.1.0', 3: '192.168.1.1', 4: '10.2.2.0', 
                                5: '192.168.2.1', 6: '10.0.4.0', 7: '192.168.4.1', 8: '10.0.2.0', 9: '10.0.2.0', 
                                10: '10.4.3.0', 11: '192.168.3.1'},                     
                    'link_idx': {0: 1, 1: 3, 2: 1, 3: 0, 4: 2, 5: 0, 6: 2, 7: 0, 8: 3, 9: 3, 10: 2, 11: 0},
                    'type': {0: 'static', 1: 'static', 2: 'dynamic', 3: 'dynamic', 4: 'dynamic', 5: 'dynamic', 6: 'dynamic', 
                             7: 'dynamic', 8: 'dynamic', 9: 'dynamic', 10: 'dynamic', 11: 'dynamic'}, 
                    'metric': {0: 10.0, 1: 10.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: 0.0, 7: 0.0, 8: 0.0, 9: 0.0, 10: 0.0, 11: 0.0}}
        utest.assertEqual(ict_net.iptables.to_dict(), expected)
        
        # test save/load and inspect with routing tables
        self.test_save_load(utest, ict_net)
        utest.assertTrue(pi.inspect(ict_net))
        return 

if __name__ == '__main__':
        
    bt = Core_Test()
               
        
    
     
        
        