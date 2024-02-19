'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from pandaict.auxiliary import pandaICTNet
import pandaict.utils as utils
from pandapower.auxiliary import ADict, get_free_id, _preserve_dtypes
from numpy import dtype, zeros
import numpy as np
import pandas as pd
from pandaict.std_types import add_basic_std_types

try:
    import pandaplan.core.pplog as logging
except ImportError:
    import logging

logger = logging.getLogger(__name__)

def create_empty_network(name="", add_stdtypes=True):
    """
    Creates an empty pandaict network datastructure.

    OPTIONAL:        
        **name** (string, None) - name for the network

        **add_stdtypes** (boolean, True) - Includes standard types to net

    OUTPUT:
        **ict_net** (attrdict) - pandaict attrdict with empty tables:

    """
    ict_net = pandaICTNet({
        "name": name,
        "node": [
            ("name", dtype(object)),
            ("type", dtype(object)),
            ("in_service", "bool"),
            ("map_to", dtype(object)),
            ("geodata", dtype(object)),
            ("link_types", dtype(object)),
            ("conversions", dtype(object)),
            ("ber", "f8"),
            ("mtbf_h", "f8"),
            ("mttr_h", "f8"),        
            ],
        "link": [
            ("name", dtype(object)),
            ("type", dtype(object)),
            ("in_service", "bool"),
            ("protocols", dtype(object)),
            ("from_node", "u4"),
            ("to_nodes", dtype(object)),
            ("map_to", dtype(object)),
            ("length_km", "f8"),           
            ],        
        "device": [
            ("name", dtype(object)),
            ("type", dtype(object)),
            ("in_service", "bool"),
            ("recv_from", "u4"),
            ("recv_items", dtype(object)),
            ("send_to", "u4"),
            ("send_items", dtype(object)),
            ("protocols", dtype(object)),
            ("map_to", dtype(object)),
            ("measures", dtype(object)),
            ("meas_accur", "f8"),
            ("controls", dtype(object)),
            ("mtbf_h", "f8"),
            ("mttr_h", "f8"),            
            ],        
        })

    if add_stdtypes:
        add_basic_std_types(ict_net)
    else:
        ict_net.std_types = {"link": {}}

    for s in ict_net:
        if isinstance(ict_net[s], list):
            ict_net[s] = pd.DataFrame(zeros(0, dtype=ict_net[s]), index=[])
    return ict_net

def create_ict_node(ict_net, name=None, type=None, index=None, in_service=True, map_to=None, geodata=None, link_types=['any'], conversions=None, ber=0, mtbf_h=0, mttr_h=0):
    if index is not None and index in ict_net["node"].index:
        raise UserWarning("A node with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["node"])

    dtypes = ict_net.node.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    lt = utils.list2str(link_types)
    mt = utils.list2str(map_to)
    cn = utils.list2str(conversions)
        
    ict_net.node.loc[index, ["name", "type", "in_service", "map_to", "geodata", "link_types", "conversions", "ber", "mtbf_h", "mttr_h"]] = [name, type, in_service, mt, geodata, lt, cn, ber, mtbf_h, mttr_h]

    _preserve_dtypes(ict_net.node, dtypes)

    return index
    
    return

def create_ict_link(ict_net, from_node, to_node, name=None, type=None, index=None, in_service=True, protocols=None, map_to=None, length_km=0 ):
    if index is not None and index in ict_net["link"].index:
        raise UserWarning("A link with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["link"])

    dtypes = ict_net.link.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    tn = utils.list2str(to_node)
    pr = utils.list2str(protocols)
    mt = utils.list2str(map_to)
        
    ict_net.link.loc[index, ["name", "type", "in_service", "from_node", "to_nodes", "protocols", "map_to",  "length_km"]] = [name, type, in_service, from_node, tn, pr, mt, length_km]

    _preserve_dtypes(ict_net.node, dtypes)

    return index
    
    

def create_ict_device(ict_net, map_to, name=None, type=None, index=None, in_service=True, protocol=None, recv_from=None, recv_items=None, send_to=None, send_items=None, send_freq=None, 
                      measures=None, meas_accur=None, controls=None, mtbf=0, mttr=0 ):
    if index is not None and index in ict_net["device"].index:
        raise UserWarning("A device with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["device"])

    dtypes = ict_net.device.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    mt = utils.list2str(map_to)
    rf = utils.list2str(recv_from)
    ri = utils.list2str(recv_items)
    st = utils.list2str(send_to) 
    si = utils.list2str(send_items) 
    sf = utils.list2str(send_freq)
    mr = utils.list2str(measures) 
    ma = utils.list2str(meas_accur)
    ct = utils.list2str(controls)    
    
        
    ict_net.link.loc[index, ["name", "type", "in_service", "map_to", "protocol", "recv_from", "recv_items", 
                             "send_to", "send_items", "send_freq", "measures", "meas_accur", "controls", 
                             "mtbf", "mttr" ]] = [name, type, in_service, mt, protocol, rf, ri, st, si, sf, mr, ma, ct, mtbf, mttr]

    _preserve_dtypes(ict_net.node, dtypes)

    return index



def autocreate_from_pp(pp_net, nodes=None, devices=None, std_link=None, check=True):
    return    

def check_net(pp_net, ict_net):
    return