'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 21.07.2025

@author: jringelstein
'''

from openpyxl import Workbook, load_workbook
import uuid
from pandaict.utils.enums import InfoItem, NodeType, DeviceType, AppType
from pandaict.pilogger import pilogger
from pandaict.create_empty_net import create_empty_network
from pandaict.create import create_ict_node, create_ict_link, create_ict_app, create_ict_connection
from pandaict.file_io import from_json
from pandaict.networks.test_networks import create_testnet1, create_testnet2, create_testnet3
import pandas as pd

def _convert_node_row(row_values, col_names):    
    conv_values = []
    for i, col in enumerate(col_names):
        if col=='type': # str to aenum NodeType
            conv_values += [NodeType[row_values[i]]]
        elif col=='in_service': # str to numpy.bool_
            conv_values += [row_values[i]=="true" or row_values[i]=="True"]
        elif col=='uuid': # str to uuid4 (?)
            conv_values += [uuid.UUID(row_values[i])]                
        elif col=='geodata': # str of form "[x,y]" to tuple (x,y)
            pass        
        elif col=='link_types': # comma separated str to list of str
            pass
        elif col=='map_to': # str to (str, int) tuple? Shift to ppict connector?? 
            pass
        else:
            conv_values += [row_values[i]]
    
    return conv_values

def ict_net_from_excel(xlsfilename):
    wb = load_workbook(filename = xlsfilename)    
    net = create_empty_network()
    #dnet = from_json("C:/Users/jringelstein/git/recode/pandaict/test/dummy.json")
    dnet = create_testnet2()
    
    ws_nodes = wb['Nodes']    
    col_names = []
    i = 0
    for row in ws_nodes.iter_rows():
        if col_names==[] and row[0].value=='index':            
            col_names = [r.value for r in row]
            nodes_df = pd.DataFrame(columns=col_names)
        elif col_names!=[]:
            print("Parse row")
            values = [r.value for r in row]        
            nodes_df.loc[i] = _convert_node_row(values, col_names)
            i += 1
            
    
    
    
        

def ict_net_to_excel(ict_net, xlsfilename):
    wb = Workbook()
    wb.save(xlsfilename)
    

def pp_net_to_excel(pp_net, xlsfilename):
    wb = Workbook()
    return wb


if __name__ == '__main__':
    ict_net_from_excel('C:/Users/jringelstein/git/recode/pandaict/src/pandaict/toolbox/template.xlsx')