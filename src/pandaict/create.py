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
            ("conversions", dtype(object)),
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

def _create_ict_node(ict_net, name=None, type=None, index=None, in_service=True, use_uuid=False, map_to=None, geodata=None, 
                     link_types=None, conversions=None, ber=0, mtbf_h=0, mttr_h=0):
    if index is not None and index in ict_net["node"].index:
        raise UserWarning("A node with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["node"])

    dtypes = ict_net.node.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    lt = utils.list2str(link_types)    
    cn = utils.list2str(conversions)
    mt = utils.tuple2str(map_to)
        
    if (use_uuid): 
        randuuid = uuid.uuid4()
    else: 
        randuuid = None
    ict_net.node.loc[index, ["name", "type", "in_service", "map_to", "geodata", "link_types", "conversions", "ber", "mtbf_h", "mttr_h", "uuid"]] = [name, type, in_service, mt, geodata, lt, cn, ber, mtbf_h, mttr_h, randuuid]

    _preserve_dtypes(ict_net.node, dtypes)

    return (index, randuuid)

def create_ict_node_with_uuid(ict_net, name=None, type=None, index=None, in_service=True, map_to=None, geodata=None, 
                              link_types=None, conversions=None, ber=0, mtbf_h=0, mttr_h=0):
    (index, uid) = _create_ict_node(ict_net, name=name, type=type, index=index, in_service=in_service, use_uuid=True, map_to=map_to, 
                                    geodata=geodata, link_types=link_types, conversions=conversions, 
                                    ber=ber, mtbf_h=mtbf_h, mttr_h=mttr_h)
    return uid

def create_ict_node(ict_net, name=None, type=None, index=None, in_service=True, map_to=None, geodata=None, link_types=None, 
                    conversions=None, ber=0, mtbf_h=0, mttr_h=0):
    (index, uid) = _create_ict_node(ict_net, name=name, type=type, index=index, in_service=in_service, use_uuid=False, map_to=map_to,
                                    geodata=geodata, link_types=link_types, conversions=conversions, 
                                    ber=ber, mtbf_h=mtbf_h, mttr_h=mttr_h)
    return index

    
def _create_ict_link(ict_net, from_elt, to_elt, name=None, type=None, index=None, in_service=True, use_uuid=False, protocols=None, 
                     map_to=None, length_km=0 ):
    if index is not None and index in ict_net["link"].index:
        raise UserWarning("A link with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["link"])

    dtypes = ict_net.link.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    if isinstance(to_elt, list): 
        tn = utils.list2str(to_elt)
    else:
        tn = [str(to_elt)]    
    pr = utils.list2str(protocols)    
    mt = utils.tuple2str(map_to)
    
    if (use_uuid): 
        randuuid = uuid.uuid4()
    else: 
        randuuid = None
        
    ict_net.link.loc[index, ["name", "type", "in_service", "from", "to", "protocols", "map_to", "length_km", "uuid"]] = [name, type, in_service, from_elt, to_elt, pr, mt, length_km, randuuid]

    _preserve_dtypes(ict_net.link, dtypes)

    return (index, randuuid)
    
def create_ict_link_with_uuid(ict_net, from_elt, to_elt, name=None, type=None, index=None, in_service=True, 
                              protocols=None, map_to=None, length_km=0 ):
    (index, uid) = _create_ict_link(ict_net, from_elt, to_elt, name, type, index, in_service=in_service, use_uuid=True, 
                                    protocols=protocols, map_to=map_to, length_km=length_km)
    return uid
    
def create_ict_link(ict_net, from_elt, to_elt, name=None, type=None, index=None, in_service=True, 
                    protocols=None, map_to=None, length_km=0 ):
    (index, uid) = _create_ict_link(ict_net, from_elt, to_elt, name, type, index, in_service=in_service, use_uuid=False, 
                                    protocols=protocols, map_to=map_to, length_km=length_km)
    return index


def _create_ict_device(ict_net, map_to, name=None, type=None, index=None, in_service=True, use_uuid=False,                        
                       measures=None, meas_accur=1, controls=None, mtbf=0, mttr=0 ):
    if index is not None and index in ict_net["device"].index:
        raise UserWarning("A device with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["device"])

    dtypes = ict_net.device.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0    
    mt = utils.tuple2str(map_to)
    mr = utils.list2str(measures)     
    ct = utils.list2str(controls)    
    
    if (use_uuid): 
        randuuid = uuid.uuid4()
    else: 
        randuuid = None
        
    ict_net.device.loc[index, ["name", "type", "in_service", "map_to", "measures", "meas_accur", "controls",                              
                             "mtbf", "mttr", "uuid" ]] = [name, type, in_service, mt, mr, meas_accur, ct, mtbf, mttr, randuuid]

    _preserve_dtypes(ict_net.device, dtypes)

    return (index, randuuid)

def create_ict_device_with_uuid(ict_net, map_to, name=None, type=None, index=None, in_service=True, 
                                measures=None, meas_accur=1, controls=None, mtbf=0, mttr=0 ):
    (index, uid) = _create_ict_device(ict_net, map_to, name=name, type=type, index=index, in_service=in_service, use_uuid=True, 
                                      measures=measures, meas_accur=meas_accur, controls=controls, mtbf=mtbf, mttr=mttr )
    return uid
    
def create_ict_device(ict_net, map_to, name=None, type=None, index=None, in_service=True, use_uuid=False,  
                      measures=None, meas_accur=1, controls=None, mtbf=0, mttr=0 ):
    (index, uid) = _create_ict_device(ict_net, map_to, name=name, type=type, index=index, in_service=in_service, use_uuid=False,  
                                      measures=measures, meas_accur=meas_accur, controls=controls, mtbf=mtbf, mttr=mttr )
    return index

def _create_ict_connection(ict_net, name=None, index=None, in_service=True, use_uuid=False, from_elt=None, to_elt=None, 
                           protocol=None, info_items=None, peers=None, producer=None, prod_freq_ms=None):    
    
    if index is not None and index in ict_net["conn"].index:
        raise UserWarning("A connection with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["conn"])

    dtypes = ict_net.conn.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    ii = utils.list2str(info_items)    
    pr = utils.list2str(producer) 
    pf = utils.list2str(prod_freq_ms)    
    
    if (use_uuid): 
        randuuid = uuid.uuid4()
    else: 
        randuuid = None
        
    ict_net.conn.loc[index, ["name", "in_service", "from", "to", "protocol", "info_items", 
                             "peers", "producer", "prod_freq_ms", "uuid" ]] = [name, in_service, from_elt, to_elt, protocol, ii, 
                              peers, pr, pf, randuuid]
    

    _preserve_dtypes(ict_net.conn, dtypes)

    return (index, randuuid) 

def create_ict_connection_with_uuid(ict_net, name=None, index=None, in_service=True, from_elt=None, to_elt=None, 
                           protocol=None, info_items=None, peers=None, producer=None, prod_freq_ms=None):    
    (index, uid) = _create_ict_connection(ict_net, name=name, index=index, in_service=in_service, use_uuid=True, 
                                          from_elt=from_elt, to_elt=to_elt, protocol=protocol, info_items=info_items, 
                                          peers=peers, producer=producer, prod_freq_ms=prod_freq_ms)
    return uid  

def create_ict_connection(ict_net, name=None, index=None, in_service=True, from_elt=None, to_elt=None, 
                          protocol=None, info_items=None, peers=None, producer=None, prod_freq_ms=None):    
    (index, uid) = _create_ict_connection(ict_net, name=name, index=index, in_service=in_service, use_uuid=False, 
                                          from_elt=from_elt, to_elt=to_elt, protocol=protocol, info_items=info_items, 
                                          peers=peers, producer=producer, prod_freq_ms=prod_freq_ms)
    return index   
  


def autocreate_from_pp(pp_net, nodes=None, devices=None, std_link=None, check=True):
    return    

def check_net(pp_net, ict_net):
    return