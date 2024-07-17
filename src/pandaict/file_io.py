'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.03.2024

@authors: jringelstein
@note: file_io is not threadsave through the use of copy.deepcopy 

'''

import pandas as pd
import json
import copy
import uuid
from pandaict import create_empty_network
from pandaict import __version__
from pandaict.utils.enums import NodeType, DeviceType, AppType, InfoItem
from pandaict.pilogger import pilogger

def __df_to_json(df):
    dfc = copy.deepcopy(df)
    for i,row in df.iterrows():
        for j, cell in enumerate(row):
            if isinstance(cell,uuid.UUID):
                dfc.iloc[i,j] = str(cell)
             
    return dfc.to_json()

def __std_type_dict_to_json(di):
    dic = copy.deepcopy(di)    
    for etype in dic.keys():
        for stdtype in dic[etype].keys():
            if 'uuid' in dic[etype][stdtype].keys():            
                dic[etype][stdtype].update({'uuid': str(dic[etype][stdtype]['uuid'])})
            if 'info_items' in dic[etype][stdtype].keys():            
                dic[etype][stdtype].update({'info_items': [{'name': ii.name, 'value': ii.value} for ii in dic[etype][stdtype]['info_items']]})
                 
    return json.dumps(dic)

def __check_index_and_uuid(df):
    
    if df.index[0].isnumeric():
        df.index = df.index.astype(int)
    
    if "uuid" in df.keys():
        for i, s in enumerate(df["uuid"]):
            df.at[i,"uuid"] = uuid.UUID(s)
    
    return df
       
       
def __to_type(df, dfkey, totype, dflist=False):
    if dfkey in df.keys():
            for i, s in enumerate(df[dfkey]):
                if s is not None:
                    if isinstance(s, dict):
                        s = s.get('value', None) # for aenums
                    if s is not None and dflist:
                        df.at[i,dfkey] = [totype(e) for e in s]
                    elif s is not None:
                        df.at[i,dfkey] = totype(s)
    return df
   
        
# def __convert_map_to(df):  
#     if 'map_to' in df.keys():
#             for i, s in enumerate(df["map_to"]):
#                 if s is not None:
#                     df.at[i,"map_to"] = tuple(s)
#     return df
                 
def __json_node_to_df(df):
        
    df = __check_index_and_uuid(df)    
    df = __to_type(df, 'type', NodeType)  
    df = __to_type(df,'map_to', tuple)   
    if 'geodata' in df.keys():
        for i, s in enumerate(df["geodata"]):
            if s is not None and not (isinstance(s, dict)):
                df.at[i,"geodata"] = tuple(s)        

    return df

def __json_device_to_df(df):
    
    df = __check_index_and_uuid(df)    
    df = __to_type(df, 'type', DeviceType)                 
    
    return df

def __json_link_to_df(df):
    
    df = __check_index_and_uuid(df)       
    df = __to_type(df, 'map_to', tuple)                            
    df = __to_type(df, 'from', tuple)
    df = __to_type(df, 'to', tuple, dflist=True)    
                        
    return df

def __json_app_to_df(df):
    
    df = __check_index_and_uuid(df)  
    df = __to_type(df, 'map_to', tuple)                    
    df = __to_type(df, 'type', AppType)        
    df = __to_type(df, 'conversions', tuple, dflist=True)
                    
    return df

def __json_conn_to_df(df):
    
    df = __check_index_and_uuid(df)       
    df = __to_type(df, 'peers', tuple)              
    df = __to_type(df, 'info_items', InfoItem, dflist=True) 
                
    return df

def __json_std_type_to_df(df):
    
    df = __check_index_and_uuid(df)       
                
    for pr in df['protocol'].keys():
        if isinstance(df['protocol'][pr], dict):
            df['protocol'][pr].update({'info_items': [InfoItem(v['value']) for v in df['protocol'][pr]['info_items']]})
            df['protocol'][pr].update({'uuid': uuid.UUID(df['protocol'][pr]['uuid'])})
    for li in df['link'].keys():
        if isinstance(df['link'][li], dict):          
            df['link'][li].update({'uuid': uuid.UUID(df['link'][li]['uuid'])})            
                
    return df

def to_json(ict_net, filename, save_std_types=False):
    """
        Saves a pandaict Network in JSON format.

        :INPUT:
            **ict_net** (dict) - The pandaict format network

            **filename** (string or file) - The absolute or relative path to the output file or file-like object

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
            if save_std_types:
                jstdt = __std_type_dict_to_json(ict_net.std_types)
            else:
                jstdt = "{}"
            json.dump({"info": "pandaICT net file", "pandaict_version": __version__, "name": ict_net.name, "connectors": ict_net.connectors[0].to_list(),                               
                        "node":       json.loads(jnode),
                        "link":       json.loads(jlink),
                        "device":     json.loads(jdevc),
                        "app":        json.loads(jappc),
                        "conn":       json.loads(jconn),
                        "std_type":   json.loads(jstdt),
                        }, pifile, indent=2)                            
        except:
            pilogger.error("Error while writing net to "+filename)  

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
        except:
            pilogger.error("Not a valid pandaICT file: "+filename)
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
    ict_net.node       = __json_node_to_df(pd.DataFrame(jall["node"]))
    ict_net.link       = __json_link_to_df(pd.DataFrame(jall["link"]))
    ict_net.device     = __json_device_to_df(pd.DataFrame(jall["device"]))
    ict_net.app        = __json_app_to_df(pd.DataFrame(jall["app"]))
    ict_net.conn       = __json_conn_to_df(pd.DataFrame(jall["conn"]))
    ict_net.std_types  = __json_std_type_to_df(pd.DataFrame(jall["std_type"])).to_dict()

    return ict_net

