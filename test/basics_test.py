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
from   pandaict.utils import uuid2elt, elt2uuid
from   pandaict.enums import NodeType
import ppcoupling
from   ppcoupling.enums import ppMeasurements as Meas
from   ppcoupling.enums import ppSetpoints as Setp
from   ppcoupling.enums import ppDeviceType
import pandas as pd
import math
import csv

class Basics_Test():
    
    def test_create_ict_net(self, utest):
        
        # -------- UC4 simple Test network ------- 
        # Creation with indexes     
        ict_net    = pi.create_empty_network("Test network",True)
        node1      = pi.create_ict_node(ict_net, name="Node1", type=NodeType.ROUTER)
        node2      = pi.create_ict_node(ict_net, name="Node2", type=NodeType.ROUTER) 
            
        conv1      = pi.create_ict_device(ict_net, name="Conv1", type=pi.DeviceType.CONVERTER) 
        conv2      = pi.create_ict_device(ict_net, name="Conv2", type=pi.DeviceType.CONVERTER) 
        conv3      = pi.create_ict_device(ict_net, name="Conv3", type=pi.DeviceType.CONVERTER) 
        
        cc         = pi.create_ict_device(ict_net, name="CC") 
        pq1        = pi.create_ict_device(ict_net, name="PQ1")  
        pq2        = pi.create_ict_device(ict_net, name="PQ2")  
        sc         = pi.create_ict_device(ict_net, name="SC")      
        pc1        = pi.create_ict_device(ict_net, name="PC1")  
        pc2        = pi.create_ict_device(ict_net, name="PC2")  
        
        link1      = pi.create_ict_link(ict_net, name="CC_Node1", type="LAN1000", from_elt=cc, to_elt=[node1], length_km=0.01)
        link2      = pi.create_ict_link(ict_net, name="Node1_Node2", type="Fiber", from_elt=node1, to_elt=[node2], length_km=25)
        link3      = pi.create_ict_link(ict_net, name="Node2_Conv1", type="ADSL8", from_elt=node2, to_elt=[conv1], length_km=5)
        link4      = pi.create_ict_link(ict_net, name="Node2_Conv2", type="LTE50", from_elt=node2, to_elt=[conv2], length_km=10)
        link5      = pi.create_ict_link(ict_net, name="Node2_Conv3", type="ADSL8", from_elt=node2, to_elt=[conv3], length_km=5)
        link6      = pi.create_ict_link(ict_net, name="Node2_PQ1", type="LAN1000", from_elt=node2, to_elt=[pq1], length_km=0.01)
        link7      = pi.create_ict_link(ict_net, name="Node2_PQ2", type="LAN1000", from_elt=node2, to_elt=[pq2], length_km=0.01)
        link8      = pi.create_ict_link(ict_net, name="Conv1_PC1", type="LAN1000", from_elt=conv1, to_elt=[pc1], length_km=0.01)
        link9      = pi.create_ict_link(ict_net, name="Conv2_PC2", type="RS485", from_elt=conv2, to_elt=[pc2], length_km=0.01)
        link10     = pi.create_ict_link(ict_net, name="Conv3_SC", type="Binary", from_elt=conv3, to_elt=[sc], length_km=0.001)
        
        conn1      = pi.create_ict_connection(ict_net, name="CC_Conv1", from_elt=cc, to_elt=conv1)                   
        conn2      = pi.create_ict_connection(ict_net, name="Conv1_PC1", from_elt=conv1, to_elt=pc1)                    
        conn3      = pi.create_ict_connection(ict_net, name="CC_PQ1", from_elt=cc, to_elt=pq1)                    
        conn4      = pi.create_ict_connection(ict_net, name="CC_Conv2", from_elt=cc, to_elt=conv2)                    
        conn5      = pi.create_ict_connection(ict_net, name="Conv2_PC2", from_elt=conv2, to_elt=pc2)                    
        conn6      = pi.create_ict_connection(ict_net, name="CC_PQ2", from_elt=cc, to_elt=pq2)                    
        conn7      = pi.create_ict_connection(ict_net, name="CC_Conv3", from_elt=cc, to_elt=conv3)            
        conn8      = pi.create_ict_connection(ict_net, name="Conv3_SC", from_elt=conv3, to_elt=sc)
                        
        ppcoupling.init_extend_network(ict_net)    
        ppcoupling.extend_ict_node(ict_net, node1, map_to=("bus", 0))
        ppcoupling.extend_ict_node(ict_net, node2, map_to=("bus", 2))
        ppcoupling.extend_ict_device(ict_net, conv1, map_to=("bus", 5))
        ppcoupling.extend_ict_device(ict_net, conv2, map_to=("bus", 6))
        ppcoupling.extend_ict_device(ict_net, conv3, map_to=("bus", 6))
        
        ppcoupling.extend_ict_device(ict_net, cc, map_to=("ext_grid", 0), type=ppDeviceType.CONTROLCENTER)
        ppcoupling.extend_ict_device(ict_net, pq1, map_to=("switch", 2), type=ppDeviceType.MEASUREMENT, controls=[], measures=["P_kW", "Q_kVA"])
        ppcoupling.extend_ict_device(ict_net, pq2, map_to=("switch", 7), type=ppDeviceType.MEASUREMENT, controls=[], measures=["P_kW", "Q_kVA"])
        ppcoupling.extend_ict_device(ict_net, sc, map_to=("bus", 6), type=ppDeviceType.ACTUATOR, controls=["closed"], measures=["closed"])
        ppcoupling.extend_ict_device(ict_net, pc1, map_to=("sgen", 1), type=ppDeviceType.CONTROLLER, controls=["P_kW", "Q_kVA"], measures=["P_kW", "Q_kVA"] )
        ppcoupling.extend_ict_device(ict_net, pc2, map_to=("sgen", 0), type=ppDeviceType.CONTROLLER, controls=["P_kW"], measures=["P_kW"] )
        
        ppcoupling.extend_ict_connection(ict_net, conn1, protocol="IEC104-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,pc1), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
        ppcoupling.extend_ict_connection(ict_net, conn2, protocol="IEC61850_MMC",
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,pc1), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
        ppcoupling.extend_ict_connection(ict_net, conn3, protocol="IEC104-TCP", 
                    info_items=[Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(pq1,cc), producer=[0,0], prod_freq_ms=[6E4, 6E4])    
        ppcoupling.extend_ict_connection(ict_net, conn4, protocol="MODBUS-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Meas.ACTIVE_POWER], 
                    peers=(cc,pc2), producer=[0,1], prod_freq_ms=[3E5, 3E5])
        ppcoupling.extend_ict_connection(ict_net, conn5, protocol="MODBUS-SMA-prop", 
                    info_items=[Setp.ACTIVE_POWER, Meas.ACTIVE_POWER], 
                    peers=(cc,pc2), producer=[0,1], prod_freq_ms=[3E5, 3E5])  
        ppcoupling.extend_ict_connection(ict_net, conn6, protocol="IEC104-TCP",
                    info_items=[Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(pq2,cc), producer=[0,0], prod_freq_ms=[6E4, 6E4])
        ppcoupling.extend_ict_connection(ict_net, conn7, protocol="IEC104-TCP", 
                    info_items=[Setp.SWITCH_POSITION, Meas.SWITCH_POSITION], 
                    peers=(cc,sc), producer=[0,1], prod_freq_ms=[])
        ppcoupling.extend_ict_connection(ict_net, conn8, protocol="Binary",
                    info_items=[Setp.SWITCH_POSITION, Meas.SWITCH_POSITION], 
                    peers=(cc,sc), producer=[0,1], prod_freq_ms=[])      
        
        # Creation with uuids   
        ict_net2   = pi.create_empty_network("Test network",True) 
        node1      = pi.create_ict_node(ict_net2, use_uuid=True, name="Node1", type=NodeType.ROUTER) 
        node2      = pi.create_ict_node(ict_net2, use_uuid=True, name="Node2", type=NodeType.ROUTER) 
        
        conv1      = pi.create_ict_device(ict_net2, use_uuid=True, name="Conv1", type=pi.DeviceType.CONVERTER)    
        conv2      = pi.create_ict_device(ict_net2, use_uuid=True, name="Conv2", type=pi.DeviceType.CONVERTER) 
        conv3      = pi.create_ict_device(ict_net2, use_uuid=True, name="Conv3", type=pi.DeviceType.CONVERTER) 
        
        cc         = pi.create_ict_device(ict_net2, use_uuid=True, name="CC")
        pq1        = pi.create_ict_device(ict_net2, use_uuid=True, name="PQ1")
        pq2        = pi.create_ict_device(ict_net2, use_uuid=True, name="PQ2")
        sc         = pi.create_ict_device(ict_net2, use_uuid=True, name="SC")    
        pc1        = pi.create_ict_device(ict_net2, use_uuid=True, name="PC1")
        pc2        = pi.create_ict_device(ict_net2, use_uuid=True, name="PC2")
        
        link1      = pi.create_ict_link(ict_net2, use_uuid=True, name="CC_Node1", type="LAN1000", from_elt=cc, to_elt=[node1], length_km=0.01)
        link2      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node1_Node2", type="Fiber", from_elt=node1, to_elt=[node2], length_km=25)
        link3      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv1", type="ADSL8", from_elt=node2, to_elt=[conv1], length_km=5)
        link4      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv2", type="LTE50", from_elt=node2, to_elt=[conv2], length_km=10)
        link5      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_Conv3", type="ADSL8", from_elt=node2, to_elt=[conv3], length_km=5)
        link6      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_PQ1", type="LAN1000", from_elt=node2, to_elt=[pq1], length_km=0.01)
        link7      = pi.create_ict_link(ict_net2, use_uuid=True, name="Node2_PQ2", type="LAN1000", from_elt=node2, to_elt=[pq2], length_km=0.01)
        link8      = pi.create_ict_link(ict_net2, use_uuid=True, name="Conv1_PC1", type="LAN1000", from_elt=conv1, to_elt=[pc1], length_km=0.01)
        link9      = pi.create_ict_link(ict_net2, use_uuid=True, name="Conv2_PC2", type="RS485", from_elt=conv2, to_elt=[pc2], length_km=0.01)
        link10     = pi.create_ict_link(ict_net2, use_uuid=True, name="Conv3_SC", type="Binary", from_elt=conv3, to_elt=[sc], length_km=0.001)
        
        conn1      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv1", from_elt=cc, to_elt=conv1)                     
        conn2      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv1_PC1", from_elt=conv1, to_elt=pc1)                     
        conn3      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_PQ1", from_elt=cc, to_elt=pq1)                    
        conn4      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv2", from_elt=cc, to_elt=conv2)                     
        conn5      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv2_PC2", from_elt=conv2, to_elt=pc2)                     
        conn6      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_PQ2", from_elt=cc, to_elt=pq2)                    
        conn7      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv3", from_elt=cc, to_elt=conv3) 
        conn8      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv3_SC", from_elt=conv3, to_elt=sc)                     
            
        ppcoupling.init_extend_network(ict_net2)    
        ppcoupling.extend_ict_node(ict_net2, node1, map_to=("bus", 0))
        ppcoupling.extend_ict_node(ict_net2, node2, map_to=("bus", 2))
        ppcoupling.extend_ict_device(ict_net2, conv1, map_to=("bus", 5))
        ppcoupling.extend_ict_device(ict_net2, conv2, map_to=("bus", 6))
        ppcoupling.extend_ict_device(ict_net2, conv3, map_to=("bus", 6))
        
        ppcoupling.extend_ict_device(ict_net2, cc, map_to=("ext_grid", 0), type=ppDeviceType.CONTROLCENTER)
        ppcoupling.extend_ict_device(ict_net2, pq1, map_to=("switch", 2), type=ppDeviceType.MEASUREMENT, controls=[], measures=["P_kW", "Q_kVA"])
        ppcoupling.extend_ict_device(ict_net2, pq2, map_to=("switch", 7), type=ppDeviceType.MEASUREMENT, controls=[], measures=["P_kW", "Q_kVA"])
        ppcoupling.extend_ict_device(ict_net2, sc, map_to=("bus", 6), type=ppDeviceType.ACTUATOR, controls=["closed"], measures=["closed"])
        ppcoupling.extend_ict_device(ict_net2, pc1, map_to=("sgen", 1), type=ppDeviceType.CONTROLLER, controls=["P_kW", "Q_kVA"], measures=["P_kW", "Q_kVA"] )
        ppcoupling.extend_ict_device(ict_net2, pc2, map_to=("sgen", 0), type=ppDeviceType.CONTROLLER, controls=["P_kW"], measures=["P_kW"] )
        
        
        ppcoupling.extend_ict_connection(ict_net2, conn1, protocol="IEC104-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,pc1), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
        ppcoupling.extend_ict_connection(ict_net2, conn2, protocol="IEC61850_MMC",
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,pc1), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
        ppcoupling.extend_ict_connection(ict_net2, conn3, protocol="IEC104-TCP", 
                    info_items=[Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(pq1,cc), producer=[0,0], prod_freq_ms=[6E4, 6E4])    
        ppcoupling.extend_ict_connection(ict_net2, conn4, protocol="MODBUS-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Meas.ACTIVE_POWER], 
                    peers=(cc,pc2), producer=[0,1], prod_freq_ms=[3E5, 3E5])
        ppcoupling.extend_ict_connection(ict_net2, conn5, protocol="MODBUS-SMA-prop", 
                    info_items=[Setp.ACTIVE_POWER, Meas.ACTIVE_POWER], 
                    peers=(cc,pc2), producer=[0,1], prod_freq_ms=[3E5, 3E5])  
        ppcoupling.extend_ict_connection(ict_net2, conn6, protocol="IEC104-TCP",
                    info_items=[Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(pq2,cc), producer=[0,0], prod_freq_ms=[6E4, 6E4])
        ppcoupling.extend_ict_connection(ict_net2, conn7, protocol="IEC104-TCP", 
                    info_items=[Setp.SWITCH_POSITION, Meas.SWITCH_POSITION], 
                    peers=(cc,sc), producer=[0,1], prod_freq_ms=[])
        ppcoupling.extend_ict_connection(ict_net2, conn8, protocol="Binary",
                    info_items=[Setp.SWITCH_POSITION, Meas.SWITCH_POSITION], 
                    peers=(cc,sc), producer=[0,1], prod_freq_ms=[])  
        
        # pi.to_json(ict_net, 'dummy.json')
        net_reloaded = pi.from_json('dummy.json')
        utest.assertTrue(ict_net.equals_excluding_uuids_and_std_types(ict_net2))   
        return   