'''
Created on 21.07.2025
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

from openpyxl import __version__ as openpyxl_version
from openpyxl import load_workbook
from openpyxl.cell import MergedCell
import os
import uuid
import numpy as np
from pandaict.utils.enums import InfoItem, NodeType, DeviceType, AppType, add_custom_enum
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

class Sheetnames:    
    ENUMS = "Custom Enums"
    LINKTYPES = "Custom Linktypes"
    PROTOCOLTYPES = "Custom Protocoltypes"

def _get_metadata(wb):
    ws = wb['Metadata']
    md = {}
    for row in ws.iter_rows():
        if row[0].value in ['name', 'connectors', 'pandaict_version', 'openpyxl_version']:
            md.update({row[0].value: row[1].value})
    return md

def _get_connector_extensions(elt_type):
    connector_extensions = {'pp_pict_connector': {'node': {'map_to': tuple},
                                                  'link': {'map_to': tuple},
                                                  'app':  {'map_to': tuple, 'measures': list, 'meas_accur': list, 'controls': list}}
                            }
    exts = {}
    for c in connectors_installed:
        if c in connector_extensions.keys() and elt_type in connector_extensions[c].keys():
            exts.update(connector_extensions[c][elt_type])
    return exts

def _bulk_extend_net(net):
    for elt_type in ['node','device','link','app','conn']:
        if elt_type not in net.keys():
            continue
        exts = _get_connector_extensions(elt_type)
        for e in exts.keys():
            net[elt_type][e] = None
    return net

def _get_default_values(sheetname):
    conv_values = {'Nodes': ["", NodeType.ROUTER,True,None,None,"all",None,None,None],
                   'Devices': ["",DeviceType.RTU,True,None,None,None],
                   'Links': ["",None,True,None,None,None,0],
                   'Connections': ["",True,None,None,None,"",[],None,[],None],
                   'Apps': ["",AppType.CLIENT,True,None,None,None]}    
    return conv_values[sheetname] or None    

# fetch column number range for "Core" or "pp_pict_connector" areas
def _get_col_range(ws, areastring):
    for row in ws.iter_rows():
        if not any(isinstance(c, MergedCell) for c in row):
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
        if not any(isinstance(c, MergedCell) for c in row):
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
        elif cname in ["link_types", "protocols", "measures", "controls"]:
            rconv = [lt.strip() for lt in rvalue.split(",")]
        elif cname in ["from","map_to"]:
            rconv = _convert_pandaelt(ctype, rconv, rvalue)
        elif cname in ["to"]:
            rconv = _convert_toelt(ctype, rconv, rvalue)
        elif cname in ["info_items"]:
            rconv = _convert_info_item(rconv, rvalue)
        elif cname in ["producer","payload_size_byte"]:
            rconv = _convert_prod_payload(rvalue)
        elif cname in ["prod_freq_ms"]:
            rconv = _convert_prodfreq(ctype, rvalue)
        elif cname in ["bandwidth_Mbps", "latency_ms"]:
            rconv = _convert_bw_lat(ctype, rvalue)
        elif cname in ["peers"]:
            speer1 = rvalue.split(";")[0].strip()
            speer2 = rvalue.split(";")[1].strip()
            rconv = ((speer1.split(",")[0].strip(), int(speer1.split(",")[1].strip())),
                     (speer2.split(",")[0].strip(), int(speer2.split(",")[1].strip())))
        elif cname in ["conversions"]:
            rconv = _convert_conversions(rvalue)
        elif rvalue is not None:
            rconv = ctype(rvalue)
    except (IndexError, AttributeError, ValueError):
        raise UserWarning("Can not convert '" + str(rvalue) + "' into "+str(ctype)+" for "+cname+".")
    return rconv


def _convert_bw_lat(ctype, rvalue):
    if isinstance(rvalue, (int, float)):
        rconv = ctype([rvalue])
    else:
        rconv = ctype([float(ii.strip()) for ii in rvalue.split(",")])
    return rconv

def _convert_prodfreq(ctype, rvalue):
    if isinstance(rvalue, (int, float)):
        rconv = ctype([rvalue])
    else:
        rconv = ctype([float(ii.strip()) for ii in rvalue.split(",")])
    if rconv==[]: 
        return None
    else:
        return rconv


def _convert_prod_payload(rvalue):
    if rvalue is None: 
        return None
    elif isinstance(rvalue, int):
        rconv = [rvalue]
    else:
        rconv = [int(ii.strip()) for ii in rvalue.split(",")]
    return rconv


def _convert_conversions(rvalue):
    rconv = []
    for p in rvalue.split(";"):
        plist = []
        for i, pitem in enumerate(p.strip().split(",")):
            if i < 2:
                plist += [pitem]
            elif pitem is not None:
                plist += [float(pitem)]
        rconv += [tuple(plist)]
    return rconv


def _convert_info_item(rconv, rvalue):
    if len(rvalue.split(",")) == 1:
        rconv = [InfoItem[rvalue.strip()]]
    elif rvalue is not None:
        rconv = [InfoItem[ii.strip()] for ii in rvalue.split(",")]
    return rconv


def _convert_toelt(ctype, rconv, rvalue):
    if ctype == list:
        rconv = [(i.split(',')[0].strip(), int(i.split(',')[1].strip())) for i in rvalue.split(';')]
    elif ctype == int:
        rconv = int(rvalue)
    return rconv


def _convert_pandaelt(ctype, rconv, rvalue):
    if ctype == tuple:
        elt = rvalue.split(',')[0].strip()
        idx = int(rvalue.split(',')[1].strip())
        rconv = (elt, idx)
    elif ctype == int:
        rconv = int(rvalue)
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

    exts = _get_connector_extensions(_get_df_name(sheetname))
    if exts:
        conv_to.update(exts)
        conv_values += [None]*len(exts.values())

    for i, col in enumerate(col_names):
        if row_values[i] is None or row_values[i]=="":
            continue
        elif col in conv_to.keys():
            conv_values[i] = _get_converted_value(row_values[i], conv_to[col], col)
        else:
            conv_values[i] = row_values[i]
    return conv_values

def _add_enums(net, row_values):
    allowed_classes = {"InfoItem": InfoItem, "NodeType": NodeType, "DeviceType": DeviceType, "AppType": AppType}
    if row_values[0] in allowed_classes.keys():
        add_custom_enum(net, allowed_classes[row_values[0]], row_values[1])

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
        elif k=='custom':
            cv = data[k]
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
        elif k=='custom':
            cv = data[k]
        data.update({k: cv})

    create_std_type(net, data=data, name=name, element="protocol")

def _get_df_name(sheetname):
    sheetname_to_df_name = {"Nodes": "node", "Devices": "device", "Links": "link", "Connections": "conn", "Apps": "app"}
    return sheetname_to_df_name[sheetname]

def _evaluate_sheet(net, wb, sheetname):

    ws = wb[sheetname]
    col_names = []

    _, _ = _get_col_range(ws, "Core")

    area = _get_col_area(ws, ["Core"]+connectors_installed)
    for row in ws.iter_rows():
        rowarea = np.array(row)[area]
        if col_names==[] and row[0].value=='index':
            col_names = [r.value for r in rowarea if r.value is not None]
        elif col_names!=[] and len(row)>0 and not all(c.value is None for c in rowarea):
            idx = row[0].value
            values = [r.value for r in rowarea]
            if sheetname==Sheetnames.ENUMS:
                _add_enums(net, values)
            elif sheetname==Sheetnames.LINKTYPES:
                _add_linktypes(net, values+[True], col_names+['custom'])
            elif sheetname==Sheetnames.PROTOCOLTYPES:
                _add_protocoltypes(net, values+[True], col_names+['custom'])
            else:
                conv_values = _convert_area(values, col_names, sheetname)
                net[_get_df_name(sheetname)].loc[idx] = conv_values
    return net


def from_excel(xlsfilename, do_inspection=True):
    """
    Load a pandaict network from an XLSX file.    

    :INPUT:
        **xlsfilename** (string or file) - The absolute or relative path to and name of the input file or file-like object

    :OUTPUT:
        **do_inspection** (boolean, default True) - If True, an inspection is done on the loaded network; if False, inspection is omitted. 
        
    :EXAMPLE:
        ict_net = from_excel("example.xlsx")
        
    """    
    wb = load_workbook(filename = xlsfilename)  
    md = _get_metadata(wb)              
    net = create_empty_network()
    net = _bulk_extend_net(net)
    net.name = md.get('name', "")
    
    for sheetname in [Sheetnames.ENUMS, Sheetnames.LINKTYPES, Sheetnames.PROTOCOLTYPES, "Nodes", "Devices", "Links", "Connections", "Apps"]:
        net = _evaluate_sheet(net, wb, sheetname)    
    passed = inspect(net, verbose=True) if do_inspection else True
    
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
            row[1].value=str(connectors_installed).replace('[','').replace(']','').strip()
        elif row[0].value=="pandaict_version":
            row[1].value=pandaict_version
        elif row[0].value=="openpyxl_version":
            row[1].value=openpyxl_version

def _convert_eltid_to_int(datatuple):
    if isinstance(datatuple[1], np.int64): 
        return (datatuple[0], int(datatuple[1]))
    else:
        return datatuple    

def _to_xls_handle_tuple(dataitem):
    if isinstance(dataitem[0], str):
        _dataitem = _convert_eltid_to_int(dataitem)            
        return str(_dataitem).replace("(","").replace(")","").replace("'","")
    elif isinstance(dataitem[0], tuple):            
        return str(dataitem).replace("),",";").replace("(","").replace(")","").replace("'","")
    else:
        return str(dataitem).replace("(","").replace(")","")

def _to_xls_handle_list(dataitem):
    if isinstance(dataitem[0], tuple):
        _dataitem = _convert_eltid_to_int(dataitem[0])            
        s = str(_dataitem).replace("[","").replace("]","").replace("'","")
        s = s.replace("),",";").replace("(","").replace(", ",",")
        if s[-1]==")":
            s = s[:-1]
        return s
    elif isinstance(dataitem[0], str):
        return str(dataitem).replace("[","").replace("]","").replace("'","")
    elif isinstance(dataitem[0], (AppType, NodeType, DeviceType, InfoItem)):
        s = [ii.name for ii in dataitem]
        return str(s).replace("[","").replace("]","").replace("'","")
    else:
        return str(dataitem).replace("[","").replace("]","")

def _to_xls_format(dataitem):
    if isinstance(dataitem, (AppType, NodeType, DeviceType, InfoItem)):
        return dataitem.name
    elif isinstance(dataitem, (bool, uuid.UUID)):
        return str(dataitem)
    elif isinstance(dataitem, tuple):
        return _to_xls_handle_tuple(dataitem)
    elif isinstance(dataitem, list):
        return _to_xls_handle_list(dataitem)
    else:
        return dataitem

def _fill_sheet(net, wb, sheetname):
    ws = wb[sheetname]
    data_to_sheet = {"Nodes": "node", "Devices": "device", "Links": "link", "Connections": "conn", "Apps": "app"}
    data_to_rows  = {"Nodes": ["name", "type", "in_service", "uuid", "geodata", "link_types", "ber", "mtbf_h", "mttr_h"],
                     "Devices": ["name", "type", "in_service", "uuid", "mtbf_h", "mttr_h"],
                     "Links": ["name", "type", "in_service", "uuid", "from", "to", "length_km"],
                     "Connections": ["name", "in_service", "uuid", "from", "to", "protocol", "info_items", "peers", "producer", "prod_freq_ms"],
                     "Apps": ["name", "type", "in_service", "uuid", "device", "conversions"],
                     Sheetnames.LINKTYPES: ["bandwidth_Mbps", "latency_ms", "wired", "protocols", "ber_per_km", "mtbf_h", "mttr_h", "uuid"],
                     Sheetnames.PROTOCOLTYPES: ["base_package_size_byte", "info_items", "payload_size_byte", "uuid"]}

    data_to_rows = _update_data_to_rows(data_to_sheet, data_to_rows)

    row_data = []  
    match sheetname:
        case Sheetnames.ENUMS:
            i = 0
            for enum_type in [NodeType, DeviceType, AppType, InfoItem]:
                for en in enum_type.__members__.items():
                    if en[1].value >= 1000:
                        row_data = [i, enum_type.__name__, en[0], en[1].value]
                        ws.append(row_data)
                        i+=1
        case Sheetnames.LINKTYPES:
            ws = _append_customtypes(net, ws, data_to_rows[sheetname], 'link')

        case Sheetnames.PROTOCOLTYPES:
            ws = _append_customtypes(net, ws, data_to_rows[sheetname], 'protocol')
        case _:    
            elt = data_to_sheet[sheetname]
            data_to_row = data_to_rows[sheetname]
            for i, ielt in net[elt].iterrows():
                row_data = [i] + [_to_xls_format(ielt[prop]) for prop in data_to_row]
                ws.append(row_data)
    return True

def _append_customtypes(net, ws, data_to_row, stype):
    i = 0
    for n, ielt in net['std_types'][stype].items():
        if 'custom' in ielt.keys():
            pdata = []
            for prop in data_to_row:                
                pdata += [_to_xls_format(ielt[prop]) if prop in ielt.keys() else None]
            row_data = [i, n] + pdata
            ws.append(row_data)
            i += 1

def _update_data_to_rows(data_to_sheet, data_to_rows):
    for s in data_to_sheet.keys():
        exts = _get_connector_extensions(data_to_sheet[s])
        if not exts:
            continue
        rdata = data_to_rows[s]
        rdata += list(exts.keys())
        data_to_rows.update({s: rdata})
    return data_to_rows

def to_excel(ict_net, xlsfilename, template_path=None):
    """
        Saves a pandaict Network in XLSX format.
        Note that, in contrast to the JSON format, built-in std_types and enums are not saved, but custom std_types and enums are always saved in the XLSX. 

        :INPUT:
            **ict_net** (dict) - The pandaict network

            **xlsfilename** (string or file) - The absolute or relative path to and name of the output file or file-like object

        :OPTIONAL:
            **template_path** (string, default None) - Absolute path to the XLSX template file ("template.xlsx") 
            
            **save_std_types** (boolean, default False) - If True, saves all non-custom std_types. If False, does not save any of them.  
            
            **save_custom_std_types** (boolean, default True) - If True, saves custom std_types regardless of save_std_types value. If False, no custom std_types are saved.  
        
        :EXAMPLE:
            to_excel(ict_net, "example.xlsx")

    """        
    if template_path==None:
        template_path = os.path.dirname(__file__).replace("\\","/")+"/"
    elif template_path != '' and template_path[-1]!='/':
        template_path += '/'
    try:
        wb = load_workbook(filename = template_path+'template.xlsx')
    except FileNotFoundError:
        msg = "Exceltools: Could not load "+template_path+"template.xlsx, network can not be saved to xlsx"
        pilogger.error(msg)
        raise UserWarning(msg)

    _fill_metadata(ict_net, wb)
    passed = False
    for sheetname in [Sheetnames.ENUMS, Sheetnames.LINKTYPES, Sheetnames.PROTOCOLTYPES, "Nodes", "Devices", "Links", "Connections", "Apps"]:
        passed = _fill_sheet(ict_net, wb, sheetname)
        if not passed:
            msg = "Exceltools: problem while filling out "+sheetname+", network can not be saved to xlsx"
            pilogger.error(msg)
            raise UserWarning(msg)

    wb.save(xlsfilename)
    pilogger.info("Exceltools: saved network to "+xlsfilename)

if __name__ == '__main__':
    net = from_excel('C:/Users/jringelstein/git/recode/pandaict/src/pandaict/toolbox/example_net.xlsx')
    to_excel(net,'example_net_rewritten.xlsx')
    net2 = from_excel('C:/Users/jringelstein/git/recode/pandaict/src/pandaict/toolbox/example_net_rewritten.xlsx')
    print(net.equals_excluding_uuids(net2))