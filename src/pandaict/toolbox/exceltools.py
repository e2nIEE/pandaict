'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 21.07.2025

@author: jringelstein
'''

from openpyxl import Workbook, load_workbook
from openpyxl.cell import MergedCell
from aenum import extend_enum
import uuid
from pandaict.utils.enums import InfoItem, NodeType, DeviceType, AppType
from pandaict.pilogger import pilogger
from pandaict.create_empty_net import create_empty_network
from pandaict.create import create_ict_node, create_ict_link, create_ict_app, create_ict_connection
from pandaict.file_io import from_json
from pandaict.networks.test_networks import create_testnet1, create_testnet2, create_testnet3
from pandaict.std_types import create_std_type
import pandas as pd

def _get_metadata(wb):
    ws = wb['Metadata']    
    md = {}    
    for row in ws.iter_rows():
        if row[0].value in ['name', 'connectors']:
            md.update({row[0].value: row[1].value}) 
    return md
        
def _get_default_values(sheetname):    
    
    conv_values = {'Nodes': ["", NodeType.ROUTER, True, None, None, "all", None, None, None],
                   'Devices': ["",DeviceType.RTU, True, None, None, None],
                   'Links': ["",None,True,None,None,None,0],
                   'Connections': ["",True,None,None,None,"",[],None,[],[]],
                   'Apps': ["",AppType.CLIENT,True,None,None,None]}    
    return conv_values[sheetname] or None    

# fetch column number range for "Core" or "pp_pict_connector" areas
def _get_col_range(ws, areastring):
    for row in ws.iter_rows():
        if not any([isinstance(c, MergedCell) for c in row]):
            continue
        values = [c.value for c in row]
        if areastring not in values:
            continue
        start_col = values.index(areastring)
        end_col = start_col+1
        while end_col<len(values) and values[end_col] is None:
            end_col += 1        
    return start_col, end_col    
    
def _get_converted_value(rvalue, ctype, cname):
    rconv = None
    try:
        if "aenum" in str(ctype):
            rconv = ctype[rvalue.upper()]
        elif ctype==bool:
            rconv = rvalue.lower()=="true"
        elif cname=="geodata":
            x = float(rvalue.split(',')[0].strip())
            y = float(rvalue.split(',')[1].strip())
            rconv = (x,y)
        elif cname in ["link_types", "protocols"]:
            rconv = [lt.strip() for lt in rvalue.split(",")]
        elif cname in ["from", "to"]:
            elt = rvalue.split(',')[0].strip()
            idx = int(rvalue.split(',')[1].strip())
            rconv = (elt,idx)
        elif cname in ["info_items"]:
            rconv = [InfoItem[ii.strip()] for ii in rvalue.split(",")]
        elif cname in ["producer"]:
            rconv = [int(ii.strip()) for ii in rvalue.split(",")]
        elif cname in ["prod_freq_ms", "bandwidth_Mbps", "latency_ms"]:
            if isinstance(rvalue, (int, float)): 
                rconv = rvalue
            else:
                rconv = ctype([float(ii.strip()) for ii in rvalue.split(",")])                  
        elif cname in ["peers"]:
            rconv = [(p.strip().split(",")[0], int(p.strip().split(",")[1])) for p in rvalue.split(";")]
        elif cname in ["conversions"]:
            rconv = []            
            for p in rvalue.split(";"):
                plist = []
                for i, pitem in enumerate(p.strip().split(",")):
                    if i<2:
                        plist += [pitem]
                    elif pitem is not None:
                        plist += [float(pitem)]
                rconv += [set(plist)]        
        elif rvalue is not None:
            rconv = ctype(rvalue)
    except (IndexError, AttributeError, ValueError):
        raise UserWarning("Can not convert '" + str(rvalue) + "' into "+str(ctype)+" for "+cname+".")
    return rconv

def _convert_area(row_values, col_names, sheetname):        
    conv_values = _get_default_values(sheetname)
    if sheetname=="Nodes":
        conv_to = {'type': NodeType, 'in_service': bool, 'uuid': uuid.UUID, 'geodata': tuple, 'link_types': list}
    elif sheetname=="Devices":
        conv_to = {'type': DeviceType, 'in_service': bool, 'uuid': uuid.UUID}
    elif sheetname=="Links":
        conv_to = {'in_service': bool, 'uuid': uuid.UUID, 'from': tuple, 'to': tuple} 
    elif sheetname=="Connections":
        conv_to = {'in_service': bool, 'uuid': uuid.UUID, 'from': tuple, 'to': tuple, 'info_items': list, 'peers': tuple, 'producer': list, 'prod_freq_ms': list} 
    elif sheetname=="Apps":
        conv_to = {'type': AppType, 'in_service': bool, 'uuid': uuid.UUID, 'conversions': list}         
            
    for i, col in enumerate(col_names):                
        if row_values[i] is None or row_values[i]=="":
            continue
        elif col in conv_to.keys(): 
            conv_values[i] = _get_converted_value(row_values[i], conv_to[col], col)                    
        else:
            conv_values[i] = row_values[i]
    
    return conv_values


def _add_enums(net, row_values, col_names):
    allowed_classes = {"InfoItem": InfoItem, "NodeType": NodeType, "DeviceType": DeviceType, "AppType": AppType}
    if row_values[0] in allowed_classes.keys():
        maxvalue = max([m.value for m in allowed_classes[row_values[0]].__members__.values()])
        newvalue = 1000 if maxvalue<1000 else maxvalue+1
        extend_enum(allowed_classes[row_values[0]], row_values[1], newvalue) 
    
def _add_linktypes(net, row_values, col_names):
    data = dict(zip(col_names, row_values))
    name = data.pop('name')
    for k in data.keys():        
        if k in ['ber_per_km', 'mtbf_h', 'mttr_h']:
            cv = _get_converted_value(data[k], float, k)
        elif k in ['bandwidth_Mbps', 'latency_ms']:
            cv = _get_converted_value(data[k], tuple, k)            
        elif k=='wired':
            cv = _get_converted_value(data[k], bool, k)
        elif k=='protocols':
            cv = _get_converted_value(data[k], list, k)
        elif k=='uuid':
            cv = _get_converted_value(data[k], uuid.UUID, k)
        data.update({k: cv})
                
    create_std_type(net, data=data, name=name, element="link")

def _add_protocoltypes(row_values, col_names):    
    print("A")
    pass

def _evaluate_sheet(net, wb, sheetname):
    
    ws = wb[sheetname]        
    col_names = []
    sheetname_to_df_name = {"Nodes": "node", "Devices": "device", "Links": "link", "Connections": "conn", "Apps": "app"}
    start_col, end_col = _get_col_range(ws, "Core")
    i = 0
    for row in ws.iter_rows():
        if col_names==[] and row[0].value=='index':            
            col_names = [r.value for r in row[start_col:end_col]]            
        elif col_names!=[] and len(row)>0:            
            idx = row[0].value
            values = [r.value for r in row[start_col:end_col]]                    
            if sheetname=="Custom Enums":
                _add_enums(net, values, col_names)
            elif sheetname=="Custom Linktypes":
                _add_linktypes(net, values, col_names)
            elif sheetname=="Custom Protocoltypes":
                _add_protocoltypes(net, values, col_names)
            else:
                conv_values = _convert_area(values, col_names, sheetname)
                net[sheetname_to_df_name[sheetname]].loc[idx] = conv_values
            i += 1                    
    return net

def ict_net_from_excel(xlsfilename):
    wb = load_workbook(filename = xlsfilename)  
    md = _get_metadata(wb)              
    net = create_empty_network()
    net.name = md.get('node', "")    
    #dnet = from_json("C:/Users/jringelstein/git/recode/pandaict/test/dummy.json")
    dnet = create_testnet2()
    
    for sheetname in ["Custom Protocoltypes"]: # ["Nodes","Devices","Links", "Connections", "Apps", "Custom Enums", "Custom Linktypes", "Custom Protocoltypes"]:
        net = _evaluate_sheet(net, wb, sheetname)
        
    print("Done")   
    
def ict_net_to_excel(ict_net, xlsfilename):
    wb = Workbook()
    wb.save(xlsfilename)
    
def pp_net_to_excel(pp_net, xlsfilename):
    wb = Workbook()
    return wb

if __name__ == '__main__':
    ref = from_json('C:/Users/jringelstein/git/recode/pandaict/test/dummy.json') # Reference test network
    ict_net_from_excel('C:/Users/jringelstein/git/recode/pandaict/src/pandaict/toolbox/example_net.xlsx')