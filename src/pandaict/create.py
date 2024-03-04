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
import uuid
from pandaict.std_types import add_basic_std_types
from pandaict.utils import list2str, tuple2str, uuid2elt, elt2uuid

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
            ("uuid", dtype(object)),
            ("map_to", dtype(object)),
            ("geodata", dtype(object)),
            ("link_types", dtype(object)),            
            ("ber", "f8"),
            ("mtbf_h", "f8"),
            ("mttr_h", "f8"),        
            ],
        "link": [
            ("name", dtype(object)),
            ("type", dtype(object)),
            ("in_service", "bool"),
            ("uuid", dtype(object)),
            ("protocols", dtype(object)),
            ("from", dtype(object)),
            ("to", dtype(object)),
            ("map_to", dtype(object)),
            ("length_km", "f8"),           
            ],        
        "device": [
            ("name", dtype(object)),
            ("type", dtype(object)),
            ("in_service", "bool"),
            ("uuid", dtype(object)),            
            ("map_to", dtype(object)),
            ("conversions", dtype(object)),
            ("measures", dtype(object)),
            ("meas_accur", "f8"),
            ("controls", dtype(object)),
            ("mtbf_h", "f8"),
            ("mttr_h", "f8"),            
            ],        
        "conn": [
            ("name", dtype(object)),
            ("in_service", "bool"),
            ("uuid", dtype(object)),
            ("from", dtype(object)),
            ("to", dtype(object)),
            ("protocol", dtype(object)),
            ("info_items", dtype(object)),
            ("peers", dtype(object)),
            ("producer", dtype(object)),
            ("prod_freq_ms", dtype(object)),
            ]
        })

    if add_stdtypes:
        add_basic_std_types(ict_net)
    else:
        ict_net.std_types = {"link": {}, "protocol": {}}

    for s in ict_net:
        if isinstance(ict_net[s], list):
            ict_net[s] = pd.DataFrame(zeros(0, dtype=ict_net[s]), index=[])
    return ict_net

def create_ict_node(ict_net, name=None, type=None, index=None, in_service=True, use_uuid=False, uid=None, 
                     map_to=None, geodata=None, link_types=None, ber=0, mtbf_h=0, mttr_h=0):
    if index is not None and index in ict_net["node"].index:
        raise UserWarning("A node with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["node"])

    dtypes = ict_net.node.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    lt = list2str(link_types)        
    mt = tuple2str(map_to)
        
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uid
    else: 
        ruuid = None
    ict_net.node.loc[index, ["name", "type", "in_service", "map_to", "geodata", "link_types", "ber", "mtbf_h", "mttr_h", "uuid"]] = [name, type, in_service, mt, geodata, lt, ber, mtbf_h, mttr_h, ruuid]

    _preserve_dtypes(ict_net.node, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('node', index)

    
def create_ict_link(ict_net, from_elt, to_elt, name=None, type=None, index=None, in_service=True, use_uuid=False, uid=None,
                    protocols=None, map_to=None, length_km=0 ):
    if index is not None and index in ict_net["link"].index:
        raise UserWarning("A link with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["link"])

    dtypes = ict_net.link.dtypes
    
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0    
    if (use_uuid):         
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uid
        from_elt = tuple2str(uuid2elt(ict_net, from_elt))
        if isinstance(to_elt, list):
            h = [tuple2str(uuid2elt(ict_net, uid)) for uid in to_elt]
            to_elt = list2str(h)
        else:
            to_elt = tuple2str(uuid2elt(ict_net, to_elt))
    else: 
        ruuid = None  
        from_elt = tuple2str(from_elt)
        if isinstance(to_elt, list):
            h = [tuple2str(elt) for elt in to_elt]
            to_elt = list2str(h)
        else:
            to_elt = tuple2str(to_elt)
          
    pr = list2str(protocols)    
    mt = tuple2str(map_to)    
        
    ict_net.link.loc[index, ["name", "type", "in_service", "from", "to", "protocols", "map_to", "length_km", "uuid"]] = [name, type, in_service, from_elt, to_elt, pr, mt, length_km, ruuid]

    _preserve_dtypes(ict_net.link, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('link', index)


def create_ict_device(ict_net, map_to, name=None, type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      conversions=None, measures=None, meas_accur=1, controls=None, mtbf=0, mttr=0 ):
    if index is not None and index in ict_net["device"].index:
        raise UserWarning("A device with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["device"])

    dtypes = ict_net.device.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0    
    mt = tuple2str(map_to)
    cn = list2str(conversions)
    mr = list2str(measures)     
    ct = list2str(controls)    
    
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uid
    else: 
        ruuid = None
        
    ict_net.device.loc[index, ["name", "type", "in_service", "map_to", "conversions", "measures", "meas_accur", "controls",                              
                             "mtbf", "mttr", "uuid" ]] = [name, type, in_service, mt, cn, mr, meas_accur, ct, mtbf, mttr, ruuid]

    _preserve_dtypes(ict_net.device, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('device', index)

def create_ict_connection(ict_net, name=None, index=None, in_service=True, use_uuid=False, uid=None,
                          from_elt=None, to_elt=None, protocol=None, info_items=None, peers=None, producer=None, prod_freq_ms=None):    
    
    if index is not None and index in ict_net["conn"].index:
        raise UserWarning("A connection with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["conn"])

    dtypes = ict_net.conn.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    ii = list2str(info_items)    
    pr = list2str(producer) 
    pf = list2str(prod_freq_ms)    
    
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uid
        # TODO: add check if peers are devices
        pdev1 = uuid2elt(ict_net, peers[0])[1]
        pdev2 = uuid2elt(ict_net, peers[1])[1] 
        pe = tuple2str( (pdev1, pdev2) )
        fe = tuple2str(uuid2elt(ict_net, from_elt))
        te = tuple2str(uuid2elt(ict_net, to_elt))
    else: 
        ruuid = None
        pe = tuple2str((peers[0][1], peers[1][1]))
        fe = tuple2str(from_elt)
        te = tuple2str(to_elt)
        
    ict_net.conn.loc[index, ["name", "in_service", "from", "to", "protocol", "info_items", 
                             "peers", "producer", "prod_freq_ms", "uuid" ]] = [name, in_service, fe, te, protocol, ii, 
                              pe, pr, pf, ruuid]
    

    _preserve_dtypes(ict_net.conn, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('conn', index)


def autocreate_from_pp(pp_net, nodes=None, devices=None, std_link=None, check=True):
    return    

def check_net(pp_net, ict_net):
    return