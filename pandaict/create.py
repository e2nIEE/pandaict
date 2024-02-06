'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from pandaict.auxiliary import pandaICTNet
from pandapower.auxiliary import ADict, get_free_id, _preserve_dtypes
from numpy import dtype, zeros
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

def create_ict_node(ict_net, name=None, type=None, index=None, in_service=True, link_types=['any']):
    if index is not None and index in ict_net["node"].index:
        raise UserWarning("A node with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["node"])

    dtypes = ict_net.node.dtypes

    ict_net.node.loc[index, ["name", "type", "in_service", "link_types"]] = [
        name, type, in_service, link_types]

    _preserve_dtypes(ict_net.node, dtypes)

    return index
    
    return

def create_ict_link(ict_net, from_node, to_nodes, length_km, name=None, type=None, index=None, in_service=True, protocols=[] ):
    return

def create_ict_device(ict_net, map_to, protocol, name=None, type=None, index=None, in_service=True,):
    return

def autocreate_from_pp(pp_net, nodes=None, devices=None, std_link=None, check=True):
    return    

def check_net(pp_net, ict_net):
    return