'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from pandaict.auxiliary import pandaICTNet
import pandaict.utils as utils
from numpy import dtype, zeros
import numpy as np
import pandas as pd
import uuid
from ppcoupling.std_types import add_basic_std_types
from pandaict.utils import list2str, tuple2str, str2list, uuid2elt, elt2uuid
from deepdiff.helper import convert_item_or_items_into_compiled_regexes_else_none

try:
    import pandaplan.core.pplog as logging
except ImportError:
    import logging

logger = logging.getLogger(__name__)

def init_extend_network(ict_net, add_stdtypes=True):
    """
    Creates an empty pandaict network datastructure.

    OPTIONAL:        
        **name** (string, None) - name for the network

        **add_stdtypes** (boolean, True) - Includes standard types to net

    OUTPUT:
        **ict_net** (attrdict) - pandaict attrdict with empty tables:

    """
    ict_net.node["map_to"] = None
    ict_net.link["map_to"] = None
    ict_net.device["map_to"] = None
    ict_net.device["measures"] = None
    ict_net.device["meas_accur"] = None
    ict_net.device["controls"] = None  

    if add_stdtypes:
        add_basic_std_types(ict_net)
    else:
        ict_net.std_types = {"link": {}, "protocol": {}}

    for s in ict_net:
        if isinstance(ict_net[s], list):
            ict_net[s] = pd.DataFrame(zeros(0, dtype=ict_net[s]), index=[])
    return ict_net

def extend_ict_node(ict_net, node_elt, map_to=None, geodata=None):
    
    if isinstance(node_elt, uuid.UUID):
        node_elt = uuid2elt(ict_net, node_elt)
        
    if not isinstance(node_elt, tuple) or not node_elt[0]=='node':
        raise UserWarning("Wrong parameter for node_elt")
        return 
        
    mt = tuple2str(map_to)
    
    ict_net.node.loc[node_elt[1], ["map_to", "geodata"]] = [mt, geodata]
    
    return 

    
def extend_ict_link(ict_net, link_elt, map_to=None):
    if isinstance(link_elt, uuid.UUID):
        link_elt = uuid2elt(ict_net, link_elt)
        
    if not isinstance(link_elt, tuple) or not link_elt[0]=='link':
        raise UserWarning("Wrong parameter for link_elt")
        return 
        
    mt = tuple2str(map_to)
    
    ict_net.link.loc[link_elt[1], ["map_to"]] = [mt]

    return


def extend_ict_device(ict_net, device_elt, map_to, type=None, measures=None, meas_accur=1, controls=None):
    if isinstance(device_elt, uuid.UUID):
        device_elt = uuid2elt(ict_net, device_elt)
        
    if not isinstance(device_elt, tuple) or not device_elt[0]=='device':
        raise UserWarning("Wrong parameter for device_elt")
        return 
        
    mt = tuple2str(map_to)
    ms = list2str(measures)
    ma = list2str(meas_accur)
    ct = list2str(controls)
    
    # retain original type
    if not type: 
        type = ict_net.device.loc[device_elt[1]]["type"]

    ict_net.device.loc[device_elt[1], ["map_to", "type", "measures", "meas_accur", "controls"]] = [mt, type, ms, ma, ct]
    
    return


def extend_ict_connection(ict_net, conn_elt, protocol=None, info_items=None, peers=None, producer=None, prod_freq_ms=None):
    if isinstance(conn_elt, uuid.UUID):
        conn_elt = uuid2elt(ict_net, conn_elt)
        
    if not isinstance(conn_elt, tuple) or not conn_elt[0]=='conn':
        raise UserWarning("Wrong parameter for conn_elt")
        return 
    
    if peers:
        if isinstance(peers[0], uuid.UUID):
            peer0 = uuid2elt(ict_net, peers[0])
            peer1 = uuid2elt(ict_net, peers[1])   
        else:
            peer0 = peers[0]
            peer1 = peers[1]
        if not (peer0[0]=='device' and peer1[0]=='device'): 
            raise UserWarning("Wrong parameter for peers (must be device elements)")
            return 
        
        
    # retain original data
    if not protocol:
         protocol = ict_net.conn.loc[conn_elt[1]]["protocol"]
    if not info_items:
        ii = ict_net.conn.loc[conn_elt[1]]["info_items"]
    else:
        ii = list2str(str2list(ict_net.conn.loc[conn_elt[1]]["info_items"]) + info_items)
    if not peers:
        ps = ict_net.conn.loc[conn_elt[1]]["peers"]
    else:
        ps = tuple2str((peer0[1], peer1[1]))
    if not producer:
        pr = ict_net.conn.loc[conn_elt[1]]["producer"]
    else:
        pr = list2str(str2list(ict_net.conn.loc[conn_elt[1]]["producer"]) + producer)
    if not prod_freq_ms:
        pf = ict_net.conn.loc[conn_elt[1]]["prod_freq_ms"]
    else:
        pf = list2str(str2list(ict_net.conn.loc[conn_elt[1]]["prod_freq_ms"]) + prod_freq_ms)
            

    ict_net.conn.loc[conn_elt[1], ["protocol", "info_items", "peers", "producer", "prod_freq_ms"]] = [protocol, ii, ps, pr, pf]
    
    return


def autocreate_from_pp(pp_net, nodes=None, devices=None, std_link=None, check=True):
    return    

def check_net(pp_net, ict_net):
    return