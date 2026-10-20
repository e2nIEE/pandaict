'''
Created on 24.01.2024

@author: jringelstein
'''

import pandapower as pp
import networkx # for graphic
import pandapower.control as control
import pandapower.timeseries as timeseries
from   pandapower.timeseries.data_sources.frame_data import DFData
import pandaict as pi
from   pandaict.enums import Measurements as Meas
from   pandaict.enums import Setpoints as Setp
from   pandaict.enums import NodeType
from   pandaict.utils import uuid2elt, elt2uuid
import pandas as pd
import math
import csv

# Suppress pandas future warning
import warnings
from enums import DeviceType
warnings.simplefilter(action='ignore', category=FutureWarning)

net = None


    
def perform_test_loadflows(): 
    global net
    cosphi_gen = 0.98
    cosphi_load = 0.95    
    
    with open('results.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        csvwriter.writerow(['pWPP','qWPP','pPV','qPV','pload','qload','vmax','vimax','vmin','vimin','lmax','limax','ltrafo'])
        for pWPP in range(0,11,1):
            # for qWPP in range(-4,4,4):
            qWPP = pWPP * math.tan(math.acos(cosphi_gen))
            for pPV in range(0,11,1):
                # for qPV in range(-4,4,4):
                qPV = pPV * math.tan(math.acos(cosphi_gen))
                for pload in range(0,13,3):
                    # for qload in range(0,25,25):
                    qload = pload * math.tan(math.acos(cosphi_load))
                    net.sgen.at[0,'p_mw'] = pPV
                    net.sgen.at[0,'q_mvar'] = qPV
                    net.sgen.at[1,'p_mw'] = pWPP
                    net.sgen.at[1,'q_mvar'] = qWPP
                    net.load.at[0,'p_mw'] = pload
                    net.load.at[0,'q_mvar'] = qload
                    pp.runpp(net, numba=False)                            
                    vmax = max(net.res_bus.vm_pu)
                    vimax = net.res_bus.vm_pu.idxmax()
                    vmin = min(net.res_bus.vm_pu)
                    vimin = net.res_bus.vm_pu.idxmin()
                    lmax = max(net.res_line.loading_percent)
                    limax = net.res_line.loading_percent.idxmax()
                    ltrafo = net.res_trafo.loading_percent.iloc[0]
                    csvwriter.writerow([str(pWPP),str(qWPP),str(pPV),str(qPV),str(pload),str(qload),str(vmax),str(vimax),str(vmin),str(vimin),str(lmax),str(limax), str(ltrafo)])
                    csvfile.flush()                        
                print("using next qWPP..")
            print("using next pWPP..")


def get_timeseries():
    
    csv_pv   = 'C:/Users/jringelstein/project/RECODE/PandaICT/UseCase4_Simple/ninja_pv_49.3715_8.2791_uncorrected.csv'
    csv_wind = 'C:/Users/jringelstein/project/RECODE/PandaICT/UseCase4_Simple/ninja_wind_49.3819_8.2616_corrected.csv'
    csv_load = 'c:/Users/jringelstein/git/recode/pandaict/test/create_simple_net/SLP_G0-M.csv'
    
    df = pd.DataFrame(index=list(range(365*24)), columns=net.sgen.index, dtype=float)    
    
    with open(csv_pv, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        i = 0
        for row in csvreader:
            if not('2022' in row[0]):
                continue            
            df.at[i,0] = float(row[2])/1000.0
            i += 1
    
    with open(csv_wind, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        i = 0
        for row in csvreader:
            if not('2022' in row[0]):
                continue            
            df.at[i,1] = float(row[2])/1000.0
            i += 1           
    
    ds = DFData(df)
    const_sgen = control.ConstControl(net, element='sgen', element_index=net.sgen.index, variable='p_mw', data_source=ds, profile_name=net.sgen.index)
    
    dfl_p = pd.DataFrame(index=list(range(365*24)), columns=net.load.index, dtype=float)
    dfl_q = pd.DataFrame(index=list(range(365*24)), columns=net.load.index, dtype=float)
    
    with open(csv_load, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=';', quotechar='|')
        i = 0
        for row in csvreader:
            if not('2016' in row[0] and ':00' in row[0]):
                continue            
            dfl_q.at[i,0] = float(row[1])*4.0
            dfl_p.at[i,0] = float(row[2])*4.0            
            i += 1   
            
    ds_p = DFData(dfl_p)
    ds_q = DFData(dfl_q)
    const_load_p = control.ConstControl(net, element='load', element_index=net.load.index, variable='p_mw', data_source=ds_p, profile_name=net.load.index)
    const_load_q = control.ConstControl(net, element='load', element_index=net.load.index, variable='q_mvar', data_source=ds_q, profile_name=net.load.index)
    
    # b = pp.create_bus(net)
    # ow = timeseries.OutputWriter(net, output_path="./", output_file_type=".xlsx")
    # ow.log_variable('res_bus', 'vm_pu')
    # ow.log_variable('res_load', 'p_mw')
    # ow.log_variable('res_load', 'q_mvar')
    # ow.log_variable('res_sgen', 'p_mw')
    # ow.log_variable('res_sgen', 'q_mvar')
    # ow.log_variable('res_line', 'loading_percent')
    # ow.log_variable('res_trafo', 'loading_percent')
    # timeseries.run_timeseries(net)
    
    #pp.to_json(net, 'UC4_simple.json')
    
    return
    
            
def generate_test_pp_network():
    global net
    net = pp.networks.example_simple()
    
    # Mod's
    #net.line.at[1,'length_km'] = 8.0
    #net.line.at[3,'length_km'] = 10.0
    pp.change_std_type(net,1,'NA2XS2Y 1x95 RM/25 12/20 kV','line')
    pp.change_std_type(net,3,'NA2XS2Y 1x95 RM/25 12/20 kV','line')    
    net.gen = net.gen.drop(0) # drop gen at bus 7        
    pp.create_sgen(net, 5, p_mw=10, q_mvar=0, sn_mva=12, name="WPP", index=1) # create new 'PV' sgen at bus 7 
    net.sgen.at[0,'name'] = 'PV' # make other sgen 'WPP' 
    net.sgen.at[0,'q_mvar'] = 0 
    net.load.at[0,'scaling'] = 1
    return

def get_pp_test_net():    
    return pp.from_json('UC4_simple.json')    

def create_test_ict_net(pp_net):
    
    # pp.to_json(net, "dummy.json")    
    
    
    # Creation with indexes
    # ict_net = pi.create_empty_network("Test network",True)
    # node1       = pi.create_ict_node(ict_net, name="Testnode1", type=NodeType.ROUTER, map_to=("bus", 10))   
    # node2       = pi.create_ict_node(ict_net, name="Testnode2", type=NodeType.ROUTER, map_to=("bus", 11))
    # link1       = pi.create_ict_link(ict_net, name="Testlink1", type="LTE50", from_elt=node1, to_elt=node2, length_km=10)
    # dev1        = pi.create_ict_device(ict_net, name="Dev1", map_to=("sgen", 5), controls=["P_kW", "Q_kVA"], measures=["P_kW","I_kA", "U_kV"])
    # dev2        = pi.create_ict_device(ict_net, name="Dev2", map_to=("trafo", 1), controls=["tap_pos"])
    #

    # -------- UC4 simple Test network ------- 
    # Creation with indexes     
    ict_net = pi.create_empty_network("Test network",True)
    node1       = pi.create_ict_node(ict_net, name="Node1", type=NodeType.ROUTER, map_to=("bus", 0))   
    node2       = pi.create_ict_node(ict_net, name="Node2", type=NodeType.ROUTER, map_to=("bus", 2))
    
    conv1       = pi.create_ict_device(ict_net, name="Conv1", type=DeviceType.CONVERTER, map_to=("bus", 5))
    conv2       = pi.create_ict_device(ict_net, name="Conv2", type=DeviceType.CONVERTER, map_to=("bus", 11))
    conv3       = pi.create_ict_device(ict_net, name="Conv3", type=DeviceType.CONVERTER, map_to=("bus", 11))
    
    cc         = pi.create_ict_device(ict_net, name="CC",  type=DeviceType.CONTROLCENTER, map_to=("ext_grid",  0), controls=[], measures=[])
    pq1        = pi.create_ict_device(ict_net, name="PQ1",  type=DeviceType.MEASUREMENT, map_to=("switch",  2), controls=[], measures=["P_kW", "Q_kVA"])
    pq2        = pi.create_ict_device(ict_net, name="PQ2",  type=DeviceType.MEASUREMENT, map_to=("switch",  7), controls=[], measures=["P_kW", "Q_kVA"])
    sc         = pi.create_ict_device(ict_net, name="SC",  type=DeviceType.ACTUATOR, map_to=("bus",  6), controls=["closed"], measures=["closed"])    
    pc1        = pi.create_ict_device(ict_net, name="PC1", type=DeviceType.CONTROLLER, map_to=("sgen", 1), controls=["P_kW", "Q_kVA"], measures=["P_kW", "Q_kVA"])
    pc2        = pi.create_ict_device(ict_net, name="PC2", type=DeviceType.CONTROLLER, map_to=("sgen", 0), controls=["P_kW"], measures=["P_kW"])
    
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
    
    conn1      = pi.create_ict_connection(ict_net, name="CC_Conv1", from_elt=cc, to_elt=conv1, protocol="IEC104-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,pc1), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
    conn2      = pi.create_ict_connection(ict_net, name="Conv1_PC1", from_elt=conv1, to_elt=pc1, protocol="IEC61850_MMC", 
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,pc1), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
    conn3      = pi.create_ict_connection(ict_net, name="CC_PQ1", from_elt=cc, to_elt=pq1, protocol="IEC104-TCP", 
                    info_items=[Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(pq1,cc), producer=[0,0], prod_freq_ms=[6E4, 6E4])    
    conn4      = pi.create_ict_connection(ict_net, name="CC_Conv2", from_elt=cc, to_elt=conv2, protocol="MODBUS-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Meas.ACTIVE_POWER], 
                    peers=(cc,pc2), producer=[0,1], prod_freq_ms=[3E5, 3E5])
    conn5      = pi.create_ict_connection(ict_net, name="Conv2_PC2", from_elt=conv2, to_elt=pc2, protocol="MODBUS-SMA-prop", 
                    info_items=[Setp.ACTIVE_POWER, Meas.ACTIVE_POWER], 
                    peers=(cc,pc2), producer=[0,1], prod_freq_ms=[3E5, 3E5])    
    conn6      = pi.create_ict_connection(ict_net, name="CC_PQ2", from_elt=cc, to_elt=pq2, protocol="IEC104-TCP", 
                    info_items=[Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(pq2,cc), producer=[0,0], prod_freq_ms=[6E4, 6E4])
    conn7      = pi.create_ict_connection(ict_net, name="CC_Conv3", from_elt=cc, to_elt=conv3, protocol="IEC104-TCP", 
                    info_items=[Setp.SWITCH_POSITION, Meas.SWITCH_POSITION], 
                    peers=(cc,sc), producer=[0,1], prod_freq_ms=[])
    conn8      = pi.create_ict_connection(ict_net, name="Conv3_SC", from_elt=conv3, to_elt=sc, protocol="Binary", 
                    info_items=[Setp.SWITCH_POSITION, Meas.SWITCH_POSITION], 
                    peers=(cc,sc), producer=[0,1], prod_freq_ms=[])        
    
    # Creation with uuids   
    ict_net2 = pi.create_empty_network("Test network",True) 
    node1       = pi.create_ict_node(ict_net2, use_uuid=True, name="Node1", type=NodeType.ROUTER, map_to=("bus", 0))   
    node2       = pi.create_ict_node(ict_net2, use_uuid=True, name="Node2", type=NodeType.ROUTER, map_to=("bus", 2))
    
    conv1       = pi.create_ict_device(ict_net2, use_uuid=True, name="Conv1", type=DeviceType.CONVERTER, map_to=("bus", 5))    
    conv2       = pi.create_ict_device(ict_net2, use_uuid=True, name="Conv2", type=DeviceType.CONVERTER, map_to=("bus", 11))
    conv3       = pi.create_ict_device(ict_net2, use_uuid=True, name="Conv3", type=DeviceType.CONVERTER, map_to=("bus", 11))
    
    cc         = pi.create_ict_device(ict_net2, use_uuid=True, name="CC",  type=DeviceType.CONTROLCENTER, map_to=("ext_grid",  0))
    pq1        = pi.create_ict_device(ict_net2, use_uuid=True, name="PQ1",  type=DeviceType.MEASUREMENT, map_to=("switch",  2), controls=[], measures=["P_kW", "Q_kVA"])
    pq2        = pi.create_ict_device(ict_net2, use_uuid=True, name="PQ2",  type=DeviceType.MEASUREMENT, map_to=("switch",  7), controls=[], measures=["P_kW", "Q_kVA"])
    sc         = pi.create_ict_device(ict_net2, use_uuid=True, name="SC",  type=DeviceType.ACTUATOR, map_to=("bus",  6), controls=["closed"], measures=["closed"])    
    pc1        = pi.create_ict_device(ict_net2, use_uuid=True, name="PC1", type=DeviceType.CONTROLLER, map_to=("sgen", 1), controls=["P_kW", "Q_kVA"], measures=["P_kW", "Q_kVA"])
    pc2        = pi.create_ict_device(ict_net2, use_uuid=True, name="PC2", type=DeviceType.CONTROLLER, map_to=("sgen", 0), controls=["P_kW"], measures=["P_kW"])
    
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
    
    conn1      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv1", from_elt=cc, to_elt=conv1, protocol="IEC104-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,pc1), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
    conn2      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv1_PC1", from_elt=conv1, to_elt=pc1, protocol="IEC61850_MMC", 
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,pc1), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
    conn3      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_PQ1", from_elt=cc, to_elt=pq1, protocol="IEC104-TCP", 
                    info_items=[Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(pq1,cc), producer=[0,0], prod_freq_ms=[6E4, 6E4])    
    conn4      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv2", from_elt=cc, to_elt=conv2, protocol="MODBUS-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Meas.ACTIVE_POWER], 
                    peers=(cc,pc2), producer=[0,1], prod_freq_ms=[3E5, 3E5])
    conn5      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv2_PC2", from_elt=conv2, to_elt=pc2, protocol="MODBUS-SMA-prop", 
                    info_items=[Setp.ACTIVE_POWER, Meas.ACTIVE_POWER], 
                    peers=(cc,pc2), producer=[0,1], prod_freq_ms=[3E5, 3E5])    
    conn6      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_PQ2", from_elt=cc, to_elt=pq2, protocol="IEC104-TCP", 
                    info_items=[Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(pq2,cc), producer=[0,0], prod_freq_ms=[6E4, 6E4])
    conn7      = pi.create_ict_connection(ict_net2, use_uuid=True, name="CC_Conv3", from_elt=cc, to_elt=conv3, protocol="IEC104-TCP", 
                    info_items=[Setp.SWITCH_POSITION, Meas.SWITCH_POSITION], 
                    peers=(cc,sc), producer=[0,1], prod_freq_ms=[])
    conn8      = pi.create_ict_connection(ict_net2, use_uuid=True, name="Conv3_SC", from_elt=conv3, to_elt=sc, protocol="Binary", 
                    info_items=[Setp.SWITCH_POSITION, Meas.SWITCH_POSITION], 
                    peers=(cc,sc), producer=[0,1], prod_freq_ms=[])
    
    
  
            
    #Creating a simple net for plot by GB
    ict_net_plot = pi.create_empty_network("Test network",True)
    
    node       = pi.create_ict_node(ict_net_plot, name="Node", type=NodeType.ROUTER, map_to=("bus", 0)) 
    
    cc         = pi.create_ict_device(ict_net_plot, name="CC",  type=DeviceType.CONTROLCENTER, map_to=("ext_grid",  0), controls=[], measures=[])
    
    conv       = pi.create_ict_device(ict_net_plot, name="Conv", type=DeviceType.CONVERTER, map_to=("bus", 5))
    
    link1      = pi.create_ict_link(ict_net_plot, name="CC_Node", type="LAN1000", from_elt=cc, to_elt=[node], length_km=0.01)
    link2      = pi.create_ict_link(ict_net_plot, name="Node_Conv", type="LTE50", from_elt=node, to_elt=[conv], length_km=5)
    
    conn      = pi.create_ict_connection(ict_net_plot, name="CC_Conv", from_elt=cc, to_elt=conv, protocol="IEC104-TCP", 
                    info_items=[Setp.ACTIVE_POWER, Setp.REACTIVE_POWER, Meas.ACTIVE_POWER, Meas.REACTIVE_POWER], 
                    peers=(cc,conv), producer=[0,0,1,1], prod_freq_ms=[-1, -1, 3E5, 3E5])
    
        
    #ict_net_reloaded = pi.from_json("UC4_simple_ict.json")
    
    # This function should compile a basic ict net structure using the provided pp net elements    
    # ict_net = pi.autocreate_from_pp(net, 
    #                              nodes = {'bus': [0,2,5,6]},
    #                              nodenames = ['Node 1', 'Node 2', 'Node 3', 'Node 4'], 
    #                              devices = {'ext_grid': [0], 'switch':[2, 7, 5], 'sgen':[1,0]},
    #                              devnames = ['CC', 'PQ1', 'PQ2', 'SC', 'PC1', 'PC2'],
    #                              std_link = 'LAN1000',                                  
    #                              links = [['CC','Node 1'], 
    #                                       ['Node 1','Node 2', 'Fiber'], 
    #                                       ['Node 2','Node 3', 'ADSL8'],
    #                                       ['Node 2','Node 4','LTE50'],
    #                                       ['Node 2','PQ1'],
    #                                       ['Node 2','PQ2'],
    #                                       ['Node 2','SC', 'ADSL8'],
    #                                       ['Node 3','PC1','LAN1000', 'IEC61850_MMS'],
    #                                       ['Node 4','PC2','LAN1000', 'MODBUS_TCP_SMA']],
    #                              std_protocol = 'IEC104_TCP',
    #                              check=True)
    
    matching = ict_net.equals_excluding_uuids_and_std_types(ict_net2)
    return ict_net, ict_net2, matching, ict_net_plot # ict_net2, matching added by GB
     
     
def check(ict_net):

    # Non-standard links used (list them)
    # Non-standard protocols used (list them) 
    # Protocols unsupported by links
    # Elements connected to non existing or non compatible elements
    # Elements with same name 
    # Nodes without connection
    # ict elements mapped to non-existing or non-fitting pp elements
    # redundant connections
        
   return 

       
if __name__ == '__main__':
    # generate_test_pp_network()
    # get_timeseries()
    net2 = pp.create_empty_network()
    net = get_pp_test_net()
    net.name = "Test network"
    ict_net, ict_net2, matching, ict_net_plot = create_test_ict_net(net) # This should create an ict net that fits the pp net ## ict_net2, matching added by GB
    #pp.to_json(net2, "dummy.json")
    pi.to_json(ict_net, "UC4_simple_ict.json")    
    ict_net_reloaded = pi.from_json("UC4_simple_ict.json")
    print(ict_net)
    print("A")
    # test_net()
    #get_timeseries()
    
    