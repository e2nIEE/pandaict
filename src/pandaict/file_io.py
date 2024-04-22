import pandas as pd
import os
import json
from numpy import int64
import csv
import pandapower as pp 
import uuid
from pandaict import create_empty_network
from pandaict import __version__
import numpy
from io import StringIO
from win32comext.internet import inetcon
from pandaict.enums import NodeType, DeviceType, AppType, InfoItem

try:
    import pplog as logging
except ImportError:
    import logging

logger = logging.getLogger(__name__)

def _df_to_json(df):
    dfc = df.copy(deep=True)
    for i,row in df.iterrows():
        for j, cell in enumerate(row):
            if isinstance(cell,uuid.UUID):
                dfc.iloc[i,j] = str(cell)
             
    return dfc.to_json()

def _json_to_df(df, dfto):
    df.index = df.index.astype(int)
    
    if "uuid" in df.keys():
        for i, s in enumerate(df["uuid"]):
            df.at[i,"uuid"] = uuid.UUID(s)    
                
    if dfto=="node":
        for i, s in enumerate(df["type"]):            
            df.at[i,"type"] = NodeType(s["value"])        
    elif dfto=="device":
        for i, s in enumerate(df["type"]):            
            df.at[i,"type"] = DeviceType(s["value"])  
    elif dfto=="app":
        for i, s in enumerate(df["type"]):            
            df.at[i,"type"] = AppType(s["value"]) 
           
    return df

def to_json(ict_net, filename, save_std_types=False):
    """
        Saves a pandaict Network in JSON format.

        INPUT:
            **ict_net** (dict) - The pandaict format network

            **filename** (string or file) - The absolute or relative path to the output file or file-like object

        EXAMPLE:

             >>> pi.to_json(ict_net, "example.json")

    """            
    with open(filename, 'w') as pifile: 
        try:
            jnode = _df_to_json(ict_net.node)
            jlink = _df_to_json(ict_net.link)
            jdevc = _df_to_json(ict_net.device)
            jappc = _df_to_json(ict_net.app)
            jconn = _df_to_json(ict_net.conn)            
            if save_std_types:
                jstdt = _df_to_json(ict_net.std_types)
            else:
                jstdt = "{}"
            jall  = json.dump({"info": "pandaICT net file", "pandaict_version": __version__, "name": ict_net.name,
                                "node":       json.loads(jnode),
                                "link":       json.loads(jlink),
                                "device":     json.loads(jdevc),
                                "app":        json.loads(jappc),
                                "conn":       json.loads(jconn),
                                "std_type":   json.loads(jstdt),
                                }, pifile, indent=2)                            
        except:
            logger.error("Error while writing net to "+filename)
            
    return  

def from_json(filename):
    """
    Load a pandaict network from a JSON file.    

    INPUT:
        **filename** (string or file) - The absolute or relative path to the input file or file-like object

    OUTPUT:
        **ict_net** (dict) - The pandaict format network

    EXAMPLE:

        >>> ict_net = pi.from_json("example.json")

    """
        
    ict_net = create_empty_network(False)
    with open(filename, 'r') as pifile: 
        try:
            jall = json.load(pifile)
        except:
            logger.error("Not a valid pandaICT file: "+filename)
            return
    
    if "pandaICT net file" not in jall['info']: 
        logger.error("Not a valid pandaICT file: "+filename)
        return    
    
    ict_net.name     = jall["name"]
    ict_net.node     = _json_to_df(pd.DataFrame(jall["node"]),"node")
    ict_net.link     = _json_to_df(pd.DataFrame(jall["link"]),"link")
    ict_net.device   = _json_to_df(pd.DataFrame(jall["device"]),"device")
    ict_net.app      = _json_to_df(pd.DataFrame(jall["app"]),"app")
    ict_net.conn     = _json_to_df(pd.DataFrame(jall["conn"]),"conn")
    ict_net.std_type = _json_to_df(pd.DataFrame(jall["std_type"]),"std_type")

    return ict_net

