'''
Created on 24.01.2024

@author: jringelstein
'''

import pandapower as pp
import pandapower.networks
import pandapower.control as control
import pandapower.timeseries as timeseries
from pandapower.timeseries.data_sources.frame_data import DFData
import pandaict as pi
import pandaict.enums as enums
from pandaict.utils import uuid2elt
import pandas as pd
import math
import csv

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
    csv_load = 'c:/Users/jringelstein/git/recode/pandaict/test/testnet/SLP_G0-M.csv'
    
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
    
    b = pp.create_bus(net)
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
    
    ict_net = pi.create_empty_network("Test network")
    
    # Creation with indexes
    # node1       = pi.create_ict_node(ict_net, name="Testnode1", type=enums.NodeType.ROUTER, map_to=("bus", 10))   
    # node2       = pi.create_ict_node(ict_net, name="Testnode2", type=enums.NodeType.ROUTER, map_to=("bus", 11))
    # link1_idx   = pi.create_ict_link(ict_net, name="Testlink1", type="LTE50", from_elt=node1, to_elt=node2, length_km=10)
    # dev1        = pi.create_ict_device(ict_net, name="Dev1", map_to=("sgen", 5), controls=["P_kW", "Q_kVA"], measures=["P_kW","I_kA", "U_kV"])
    # dev2        = pi.create_ict_device(ict_net, name="Dev2", map_to=("trafo", 1), controls=["tap_pos"])
    #

    # Creation with uuids    
    node1       = pi.create_ict_node_with_uuid(ict_net, name="Testnode1", type=enums.NodeType.ROUTER, map_to=("bus", 10))   
    node2       = pi.create_ict_node_with_uuid(ict_net, name="Testnode2", type=enums.NodeType.ROUTER, map_to=("bus", 11))
    uuid2elt(ict_net, node1)
    # link1_idx   = pi.create_ict_link_with_uuid(ict_net, name="Testlink1", type="LTE50", from_elt=node1, to_elt=node2, length_km=10)
    # dev1        = pi.create_ict_device_with_uuid(ict_net, name="Dev1", map_to=("sgen", 5), controls=["P_kW", "Q_kVA"], measures=["P_kW","I_kA", "U_kV"])
    # dev2        = pi.create_ict_device_with_uuid(ict_net, name="Dev2", map_to=("trafo", 1), controls=["tap_pos"])
    
    
    
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
    
    
    return ict_net
            
if __name__ == '__main__':
    net = get_pp_test_net()
    net.name = "Test network"
    ict_net = create_test_ict_net(net) # This should create an ict net that fits the pp net
        
    print("A")
    
    # test_net()
    #get_timeseries()
    
    