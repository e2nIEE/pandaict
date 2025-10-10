'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 21.07.2025

@author: jringelstein
'''

from openpyxl import __version__ as openpyxl_version 
from openpyxl import load_workbook
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
from pandaict.diagnosis import inspect
from pandaict import __version__ as pandaict_version 
from pandaict import connectors_installed
import pandas as pd

def _get_metadata(wb):
    ws = wb['Metadata']    
    md = {}    
    for row in ws.iter_rows():
        if row[0].value in ['name', 'connectors', 'pandaict_version', 'openpyxl_version']:
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

# fetch column area for list of areas 
def _get_col_area(ws, arealist):
    for row in ws.iter_rows():
        if not any([isinstance(c, MergedCell) for c in row]):
            continue
        values = [c.value for c in row]
        areamap = []
        add_cell=False
        for i in range(0,len(values)):
            if values[i] is not None:            
                if values[i] in arealist:
                    add_cell=True
                else:
                    add_cell=False
            areamap += [add_cell]
        break              
    return areamap    
    
   
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
        elif cname in ["from"]:
            if ctype==tuple: 
                elt = rvalue.split(',')[0].strip()
                idx = int(rvalue.split(',')[1].strip())
                rconv = (elt,idx)
            elif ctype==int:
                rconv = int(rvalue)
        elif cname in ["to"]:
            if ctype==list: 
                rconv=[(i.split(',')[0].strip(), int(i.split(',')[1].strip())) for i in rvalue.split(';')]
            elif ctype==int:
                rconv=int(rvalue)
        elif cname in ["info_items"]:   
            if len(rvalue.split(","))==1:          
                rconv = InfoItem[rvalue.strip()]
            elif rvalue is not None:
                rconv = [InfoItem[ii.strip()] for ii in rvalue.split(",")]
        elif cname in ["producer","payload_size_byte"]:
            rconv = [int(ii.strip()) for ii in rvalue.split(",")]
        elif cname in ["prod_freq_ms", "bandwidth_Mbps", "latency_ms"]:
            if isinstance(rvalue, (int, float)): 
                rconv = rvalue
            else:
                rconv = ctype([float(ii.strip()) for ii in rvalue.split(",")])                  
        elif cname in ["peers"]:
            rconv = (int(rvalue.strip().split(",")[0]), int(rvalue.strip().split(",")[1]))
        elif cname in ["conversions"]:
            rconv = []            
            for p in rvalue.split(";"):
                plist = []
                for i, pitem in enumerate(p.strip().split(",")):
                    if i<2:
                        plist += [pitem]
                    elif pitem is not None:
                        plist += [float(pitem)]
                rconv += [tuple(plist)]        
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
        conv_to = {'in_service': bool, 'uuid': uuid.UUID, 'from': tuple, 'to': list} 
    elif sheetname=="Connections":
        conv_to = {'in_service': bool, 'uuid': uuid.UUID, 'from': int, 'to': int, 'info_items': list, 'peers': tuple, 'producer': list, 'prod_freq_ms': list} 
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
    if "custom_enums" not in net.keys():
        net.custom_enums = pd.DataFrame(columns=['name', 'type', 'value'])
    if row_values[0] in allowed_classes.keys():
        if row_values[1] not in [m.name for m in allowed_classes[row_values[0]].__members__.values()]:  # if enum doesn't exist           
            maxvalue = max([m.value for m in allowed_classes[row_values[0]].__members__.values()])
            newvalue = 1000 if maxvalue<1000 else maxvalue+1
            extend_enum(allowed_classes[row_values[0]], row_values[1], newvalue) 
        else:
            newvalue = allowed_classes[row_values[0]][row_values[1]].value # if anready existing, still add it to net custom enums
        net.custom_enums.loc[len(net.custom_enums)] = [row_values[1], row_values[0], newvalue]
    
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

def _add_protocoltypes(net, row_values, col_names):    
    data = dict(zip(col_names, row_values))
    name = data.pop('name')
    for k in data.keys():               
        if k=='base_package_size_byte':
            cv = _get_converted_value(data[k], int, k)
        elif k=='payload_size_byte':
            cv = _get_converted_value(data[k], list, k)
        elif k=='info_items':
            cv = _get_converted_value(data[k], list, k)
        elif k=='uuid':
            cv = _get_converted_value(data[k], uuid.UUID, k)
        data.update({k: cv})
                
    create_std_type(net, data=data, name=name, element="protocol")
    

def _evaluate_sheet(net, wb, sheetname):
    
    ws = wb[sheetname]        
    col_names = []
    sheetname_to_df_name = {"Nodes": "node", "Devices": "device", "Links": "link", "Connections": "conn", "Apps": "app"}
    start_col, end_col = _get_col_range(ws, "Core")
    if sheetname=="Nodes":
        connectors_installed=["pp_pict_connector"] # DEBUG
        area = _get_col_area(ws, ["Core"]+connectors_installed)    
    for row in ws.iter_rows():
        if col_names==[] and row[0].value=='index':            
            col_names = [r.value for r in row[start_col:end_col]]            
        elif col_names!=[] and len(row)>0 and not all([c.value is None for c in row[start_col:end_col]]):            
            idx = row[0].value
            values = [r.value for r in row[start_col:end_col]]                    
            if sheetname=="Custom Enums":
                _add_enums(net, values, col_names)
            elif sheetname=="Custom Linktypes":
                _add_linktypes(net, values+[True], col_names+['custom'])
            elif sheetname=="Custom Protocoltypes":
                _add_protocoltypes(net, values+[True], col_names+['custom'])
            else:
                conv_values = _convert_area(values, col_names, sheetname)
                net[sheetname_to_df_name[sheetname]].loc[idx] = conv_values            
    return net

def ict_net_from_excel(xlsfilename):
    wb = load_workbook(filename = xlsfilename)  
    md = _get_metadata(wb)              
    net = create_empty_network()
    net.name = md.get('name', "")    
    #dnet = from_json("C:/Users/jringelstein/git/recode/pandaict/test/dummy.json")
    #dnet = create_testnet2()
    
    for sheetname in ["Custom Enums", "Custom Linktypes", "Custom Protocoltypes", "Nodes", "Devices", "Links", "Connections", "Apps"]:
        net = _evaluate_sheet(net, wb, sheetname)
        
    passed = inspect(net, verbose=True)
    if passed: 
        pilogger.info("Exceltools: loaded network from "+xlsfilename+", inspection passed")
    else:
        pilogger.warning("Exceltools: loaded network from "+xlsfilename+" failed inspection.")
    
    return net

def _fill_metadata(net, wb):
    ws = wb['Metadata']
    for row in ws.iter_rows():
        if row==None or len(row)==0: 
            continue
        if row[0].value=="name":
            row[1].value=net['name']
        elif row[0].value=="connectors" and len(connectors_installed)>0:            
            row[1].value=connectors_installed
        elif row[0].value=="pandaict_version":
            row[1].value=pandaict_version
        elif row[0].value=="openpyxl_version":
            row[1].value=openpyxl_version

def _to_xls_format(dataitem):
    if isinstance(dataitem, (AppType, NodeType, DeviceType, InfoItem)):
        return dataitem.name
    elif isinstance(dataitem, tuple) and isinstance(dataitem[0], str):
        return str(dataitem).replace("(","").replace(")","").replace("'","")
    elif isinstance(dataitem, tuple):
        return str(dataitem).replace("(","").replace(")","")
    elif isinstance(dataitem, list) and isinstance(dataitem[0], tuple):
        s = str(dataitem).replace("[","").replace("]","").replace("'","")
        s = s.replace("),",";").replace("(","").replace(", ",",")
        if s[-1]==")": 
            s = s[:-1]
        return s
    elif isinstance(dataitem, list) and isinstance(dataitem[0], str):
        return str(dataitem).replace("[","").replace("]","").replace("'","")
    elif isinstance(dataitem, list) and isinstance(dataitem[0], (AppType, NodeType, DeviceType, InfoItem)):        
        s = [ii.name for ii in dataitem]
        return str(s).replace("[","").replace("]","").replace("'","")
    elif isinstance(dataitem, list):
        return str(dataitem).replace("[","").replace("]","")
    elif isinstance(dataitem, (bool, uuid.UUID)):
        return str(dataitem)    
    else:
        return dataitem

def _fill_sheet(net, wb, sheetname):
    ws = wb[sheetname]       
    # data_to_sheet = {"node": "Nodes", "device": "Devices", "link": "Links", "conn": "Connections", "app": "Apps"}
    data_to_sheet = {"Nodes": "node", "Devices": "device", "Links": "link", "Connections": "conn", "Apps": "app"}
    data_to_rows  = {"Nodes": ["name", "type", "in_service", "uuid", "geodata", "link_types", "ber", "mtbf_h", "mttr_h"],
                     "Devices": ["name", "type", "in_service", "uuid", "mtbf_h", "mttr_h"],
                     "Links": ["name", "type", "in_service", "uuid", "from", "to", "length_km"],
                     "Connections": ["name", "in_service", "uuid", "from", "to", "protocol", "info_items", "peers", "producer", "prod_freq_ms"],
                     "Apps": ["name", "type", "in_service", "uuid", "device", "conversions"],
                     "Custom Linktypes": ["bandwidth_Mbps", "latency_ms", "wired", "protocols", "ber_per_km", "mtbf_h", "mttr_h", "uuid"],
                     "Custom Protocoltypes": ["base_package_size_byte", "info_items", "payload_size_byte", "uuid"]}
    
    col_names = []                           
    start_col, end_col = _get_col_range(ws, "Core")    
    for row in ws.iter_rows():
        if col_names==[] and row[0].value=='index':            
            col_names = [r.value for r in row[start_col:end_col]]            
    
    row_data = []
    if sheetname=="Custom Enums":
        i = 0
        for enum_type in [NodeType, DeviceType, AppType, InfoItem]:
            for en in enum_type.__members__.items():
                if en[1].value >= 1000: 
                    row_data = [i, enum_type.__name__, en[0], en[1].value]
                    ws.append(row_data)
                    i+=1       
    elif sheetname=="Custom Linktypes": 
        data_to_row = data_to_rows[sheetname]
        i = 0
        for n, ielt in net['std_types']['link'].items():  
            if 'custom' in ielt.keys():
                row_data = [i, n] + [_to_xls_format(ielt[prop]) for prop in data_to_row]
                ws.append(row_data)
                i+=1  
    elif sheetname=="Custom Protocoltypes": 
        data_to_row = data_to_rows[sheetname]
        i = 0
        for n, ielt in net['std_types']['protocol'].items():  
            if 'custom' in ielt.keys():
                row_data = [i, n] + [_to_xls_format(ielt[prop]) for prop in data_to_row]
                ws.append(row_data)
                i+=1          
    else:        
        elt = data_to_sheet[sheetname]    
        data_to_row = data_to_rows[sheetname]
        for i, ielt in net[elt].iterrows():  
            row_data = [i] + [_to_xls_format(ielt[prop]) for prop in data_to_row]
            ws.append(row_data)    
                
    return True
    
         
def ict_net_to_excel(net, xlsfilename, template_path=''):
    if template_path != '' and template_path[-1]!='/': 
        template_path += '/'
    try:
        wb = load_workbook(filename = template_path+'template.xlsx')
    except:
        msg = "Exceltools: Could not load "+template_path+"template.xlsx, network can not be saved to xlsx"
        pilogger.error(msg)
        raise UserWarning(msg)  
    
    _fill_metadata(net, wb)
    passed = False
    for sheetname in ["Custom Enums", "Custom Linktypes", "Custom Protocoltypes", "Nodes", "Devices", "Links", "Connections", "Apps"]:
        passed = _fill_sheet(net, wb, sheetname)
        if not passed: 
            msg = "Exceltools: problem while filling out "+sheetname+", network can not be saved to xlsx"
            pilogger.error(msg)
            raise UserWarning(msg) 
    
    wb.save(xlsfilename)
    pilogger.info("Exceltools: saved network to "+xlsfilename)
    
if __name__ == '__main__':
    # ref = from_json('C:/Users/jringelstein/git/recode/pandaict/test/dummy.json') # Reference test network
    net = ict_net_from_excel('C:/Users/jringelstein/git/recode/pandaict/src/pandaict/toolbox/example_net.xlsx')
    ict_net_to_excel(net,'example_net_rewritten.xlsx')
    net2 = ict_net_from_excel('C:/Users/jringelstein/git/recode/pandaict/src/pandaict/toolbox/example_net_rewritten.xlsx')
    print(net.equals_excluding_uuids(net2))