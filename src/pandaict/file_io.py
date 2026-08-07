'''
Created on 8.03.2024
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause

'''

import pandas as pd
import json
import copy
import uuid
from math import isnan
from pandaict import create_empty_network
from pandaict import __version__
from pandaict.utils.enums import NodeType, DeviceType, AppType, InfoItem, add_custom_enum
from pandaict.pilogger import pilogger
from json import JSONDecodeError
from aenum import extend_enum

def __df_to_json(df):
    dfc = copy.deepcopy(df)
    for i,row in df.iterrows():
        for j, cell in enumerate(row):
            if isinstance(cell,uuid.UUID):
                dfc.iloc[i,j] = str(cell)
             
    return dfc.to_json()

def __std_type_dict_to_json(di, save_std_types, save_custom_std_types):
    dic = copy.deepcopy(di)    
    for etype in di.keys():                
        for stdtype in di[etype].keys():
            if ((not save_std_types and save_custom_std_types and ("custom" not in di[etype][stdtype].keys())) # save custom only
                or (save_std_types and not save_custom_std_types and ("custom" in di[etype][stdtype].keys()))): # save non-custom only                
                dic[etype].pop(stdtype)
                continue                            
            if 'uuid' in dic[etype][stdtype].keys():            
                if dic[etype][stdtype]['uuid'] is not None:                
                    dic[etype][stdtype].update({'uuid': str(dic[etype][stdtype]['uuid'])})                
            if 'info_items' in dic[etype][stdtype].keys():            
                dic[etype][stdtype].update({'info_items': [{'name': ii.name, 'value': ii.value} for ii in dic[etype][stdtype]['info_items']]})                    
    return json.dumps(dic)

def __custom_enums_to_json():
    dic = [] 
    enum_types = [NodeType, DeviceType, AppType, InfoItem]
    for et in enum_types:
        for e in et.__iter__():
            if (e.value >= 1000):                                
                dic += [{'type': et.__name__, 'name': e.name, 'value': e.value}]
    return json.dumps(dic) 

def __check_index_and_uuid(df):
    
    if df.index[0].isnumeric():
        df.index = df.index.astype(int)    
    
    if "uuid" in df.keys():       
        uuids_str = list(df["uuid"].values)
        uuids = []
        df.drop(columns=["uuid"], inplace=True)        
        for s in uuids_str: 
            if s:
                uuids.append(uuid.UUID(s))
            else:
                uuids.append(None)
        df.insert(3, "uuid", uuids)       

    return df
       
       
def __to_type(df, dfkey, totype, dflist=""):
    if dfkey in df.keys():
        for i, s in enumerate(df[dfkey]):
            if s is None:
                continue
            if isinstance(s, dict):
                s = s.get('value', None) # for aenums
            if (dflist=="list" or dflist=="tuple"):
                if isinstance(s[0], dict):                                                    
                    df.at[i,dfkey] = [totype(e.get('value',None)) for e in s]  # for aenums
                elif dflist=="list":
                    df.at[i,dfkey] = [totype(e) for e in s]                        
                else:
                        if (isinstance(s[0], list) or isinstance(s[0], tuple)):
                            df.at[i,dfkey] = tuple([totype(e) for e in s])
                        else:
                            df.at[i,dfkey] = totype(s)                                                            
            else:
                df.at[i,dfkey] = totype(s)
    return df
        
        
def __convert_geodata(df):
    if 'geodata' in df.keys():
        for i, s in enumerate(df["geodata"]):
            if s is not None and not (isinstance(s, dict)):
                df.at[i,"geodata"] = tuple(s)
    return df

def __list_to_tuple(d, k):
    if not isinstance(d, dict):
        return d
    v = d[k]
    if isinstance(v, list):
        d.update({k: tuple(v)})
    return d
    
def __convert_std_types(df):
    for pr in df['protocol'].keys():        
        if isinstance(df['protocol'][pr], dict):
            df['protocol'][pr].update({'info_items': [InfoItem(v['value']) for v in df['protocol'][pr]['info_items']]})
            if ('uuid' in df['protocol'][pr].keys()) and (df['protocol'][pr]['uuid'] is not None):
                df['protocol'][pr].update({'uuid': uuid.UUID(df['protocol'][pr]['uuid'])})           
    for li in df['link'].keys():        
        if isinstance(df['link'][li], dict):          
            if ('uuid' in df['link'][li].keys()) and (df['link'][li]['uuid'] is not None):
                df['link'][li].update({'uuid': uuid.UUID(df['link'][li]['uuid'])})
            __list_to_tuple(df['link'][li], 'bandwidth_Mbps')
            __list_to_tuple(df['link'][li], 'latency_ms')                                       
    return df

def __json_to_enum(ict_net, df):
    str_to_type = {'NodeType': NodeType, 'DeviceType': DeviceType, 'AppType':AppType, 'InfoItem': InfoItem}
    for i, e in df.iterrows():        
        etype = str_to_type[e['type']]
        add_custom_enum(ict_net, etype, e['name'], e['value'])
    return df
                
def __json_to_df(df, elt_type):
    if df.empty:
        return df
    df = __check_index_and_uuid(df)
    if elt_type in ["node","link","app"]:
        df = __to_type(df,'map_to', tuple)        
    if elt_type=="node":
        df = __to_type(df, 'type', NodeType)          
        df = __convert_geodata(df)
    elif elt_type=="device":
        df = __to_type(df, 'type', DeviceType)
    elif elt_type=="link":                                
        df = __to_type(df, 'from', tuple)
        df = __to_type(df, 'to', tuple, dflist="list")
    elif elt_type=="app":                        
        df = __to_type(df, 'type', AppType)        
        df = __to_type(df, 'conversions', tuple, dflist="list")     
    elif elt_type=="conn":
        df = __to_type(df, 'peers', tuple, dflist="tuple")              
        df = __to_type(df, 'info_items', InfoItem, dflist="list")       
    elif elt_type=="std_type":
        df = __convert_std_types(df)       
    return df

def to_json(ict_net, filename, save_std_types=False, save_custom_std_types=True):
    """
        Saves a pandaict Network in JSON format.
        Note that custom enums are always saved, while for standard types saving options may be configured. 

        :INPUT:
            **ict_net** (dict) - The pandaict network

            **filename** (string or file) - The absolute or relative path to  and name of the output file or file-like object

        :OPTIONAL:
        
            **save_std_types** (boolean, default False) - If True, saves all non-custom std_types. If False, does not save any of them.  
            
            **save_custom_std_types** (boolean, default True) - If True, saves custom std_types regardless of save_std_types value. If False, no custom std_types are saved.  
        
        :EXAMPLE:
            pi.to_json(ict_net, "example.json")

    """            
    with open(filename, 'w') as pifile: 
        try:
            jconn = __df_to_json(ict_net.connectors)
            jnode = __df_to_json(ict_net.node)
            jlink = __df_to_json(ict_net.link)
            jdevc = __df_to_json(ict_net.device)
            jappc = __df_to_json(ict_net.app)
            jconn = __df_to_json(ict_net.conn)            
            jstdt = __std_type_dict_to_json(ict_net.std_types, save_std_types, save_custom_std_types) if (save_std_types or save_custom_std_types) else "{}"
            jcenm = __custom_enums_to_json()
            jipta = __df_to_json(ict_net.iptables) if "iptables" in ict_net.keys() else "{}"
            json.dump({"info": "pandaICT net file", "pandaict_version": __version__, "name": ict_net.name, "connectors": ict_net.connectors[0].to_list(),                               
                        "node":       json.loads(jnode),
                        "link":       json.loads(jlink),
                        "device":     json.loads(jdevc),
                        "app":        json.loads(jappc),
                        "conn":       json.loads(jconn),
                        "std_type":   json.loads(jstdt),
                        "cenum":      json.loads(jcenm),
                        "iptables":   json.loads(jipta),
                        }, pifile, indent=2)                            
        except (TypeError, IndexError, ValueError, NameError) as e:
            pilogger.error("Error while writing net to "+filename+" - "+str(e))  
            
def __remove_nans_from_std_types(std_type_dict):
    std_type_nonans = {'link': {}, 'protocol': {}}
    std_type_nonans['link'].update({k: v for k, v in std_type_dict['link'].items() if not (isinstance(v, float) and isnan(v))})
    std_type_nonans['protocol'].update({k: v for k, v in std_type_dict['protocol'].items() if not (isinstance(v, float) and isnan(v))})
    return std_type_nonans    
    

def from_json(filename):
    """
    Load a pandaict network from a JSON file.    

    :INPUT:
        **filename** (string or file) - The absolute or relative path to the input file or file-like object

    :OUTPUT:
        **ict_net** (dict) - The pandaict format network
        
    :EXAMPLE:
        ict_net = pi.from_json("example.json")
        
    """    
    ict_net = create_empty_network(False)
    with open(filename, 'r') as pifile: 
        try:
            jall = json.load(pifile)
        except (ValueError, TypeError, IOError, OSError) as e:
            pilogger.error("Not a valid pandaICT file: "+filename+" - "+str(e))
            return
    
    if "pandaICT net file" not in jall['info']: 
        pilogger.error("Not a valid pandaICT file: "+filename)
        return    
    
    ict_net.name       = jall["name"]        
    ict_net.connectors = pd.DataFrame(jall['connectors'])
    from pandaict import connectors_installed # NOTE: leave this here. It won't work if moved to the top.
    if not ict_net.connectors.empty:
        for s in ict_net.connectors[0]:
            if s not in connectors_installed:
                pilogger.warning("Network file "+filename+" uses connector "+s+" which is currently not installed")
                print("Warning: Network file "+filename+" uses connector "+s+" which is currently not installed")
    ict_net.node       = __json_to_df(pd.DataFrame(jall["node"]),"node")
    ict_net.link       = __json_to_df(pd.DataFrame(jall["link"]),"link")
    ict_net.device     = __json_to_df(pd.DataFrame(jall["device"]),"device")
    ict_net.app        = __json_to_df(pd.DataFrame(jall["app"]),"app")
    ict_net.conn       = __json_to_df(pd.DataFrame(jall["conn"]),"conn")
    if not pd.DataFrame(jall["std_type"]).empty:
        ict_net.std_types  = __json_to_df(pd.DataFrame(jall["std_type"]),"std_type").to_dict()
        ict_net.std_types  = __remove_nans_from_std_types(ict_net.std_types)
    if not pd.DataFrame(jall["cenum"]).empty:
        __json_to_enum(ict_net, pd.DataFrame(jall["cenum"]))
    if not pd.DataFrame(jall["iptables"]).empty:
        ict_net.iptables   = __json_to_df(pd.DataFrame(jall["iptables"]),"iptables")

    return ict_net

