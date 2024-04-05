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
from debugpy._vendored.pydevd.stubs._django_manager_body import none

try:
    import pandaplan.core.pplog as logging
except ImportError:
    import logging

logger = logging.getLogger(__name__)

def create_empty_network(name="", add_stdtypes=True):
    """
    Creates an empty pandaict core network datastructure.

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
            ("length_km", "f8"),           
            ],        
        "device": [
            ("name", dtype(object)),
            ("type", dtype(object)),
            ("in_service", "bool"),
            ("uuid", dtype(object)),                                
            ("mtbf_h", "f8"),
            ("mttr_h", "f8"),            
            ],  
        "app": [
            ("name", dtype(object)),
            ("type", dtype(object)),
            ("in_service", "bool"),
            ("uuid", dtype(object)),           
            ("device", "u4"), 
            ("conversions", dtype(object))                                    
            ],       
        "conn": [
            ("name", dtype(object)),
            ("in_service", "bool"),
            ("uuid", dtype(object)),
            ("from", "u4"),
            ("to", "u4"),
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
                     geodata=None, link_types=None, ber=0, mtbf_h=0, mttr_h=0):
    if index is not None and index in ict_net["node"].index:
        raise UserWarning("A node with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["node"])

    dtypes = ict_net.node.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    lt = list2str(link_types)        
           
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uid
    else: 
        ruuid = None
    ict_net.node.loc[index, ["name", "type", "in_service", "geodata", "link_types", "ber", "mtbf_h", "mttr_h", "uuid"]] = [name, type, in_service, geodata, lt, ber, mtbf_h, mttr_h, ruuid]

    _preserve_dtypes(ict_net.node, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('node', index)

    
def create_ict_link(ict_net, from_elt, to_elt, name=None, type=None, index=None, in_service=True, use_uuid=False, uid=None,
                    protocols=None, length_km=0 ):
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
        
    # TODO: check if from_elt == to_elt
    ict_net.link.loc[index, ["name", "type", "in_service", "from", "to", "protocols", "length_km", "uuid"]] = [name, type, in_service, from_elt, to_elt, pr, length_km, ruuid]

    _preserve_dtypes(ict_net.link, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('link', index)


def create_ict_device(ict_net, name=None, type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      mtbf=0, mttr=0 ):
    if index is not None and index in ict_net["device"].index:
        raise UserWarning("A device with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["device"])

    dtypes = ict_net.device.dtypes
           
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uid
    else: 
        ruuid = None
        
    ict_net.device.loc[index, ["name", "type", "in_service", "mtbf", "mttr", "uuid" ]] = [name, type, in_service, mtbf, mttr, ruuid]

    _preserve_dtypes(ict_net.device, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('device', index)
    
    
def create_ict_app(ict_net, name=None, type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      conversions=None, device=None ):
    if index is not None and index in ict_net["app"].index:
        raise UserWarning("An app with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["app"])

    dtypes = ict_net.app.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0        
    cn = list2str(conversions)
        
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uid
        rdevice = uuid2elt(ict_net, device)[1] # TODO: add element type check, expect device
    else: 
        ruuid = None
        rdevice = device[1] # TODO: add element type check, expect device
        
    ict_net.app.loc[index, ["name", "type", "in_service", "conversions", "uuid", "device" ]] = [name, type, in_service, cn, ruuid, rdevice]

    _preserve_dtypes(ict_net.app, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('app', index)


def create_ict_devapp(ict_net, name=None, devtype=None, apptype=None, in_service=True, use_uuid=False, uid=None,                      
                      conversions=None, mtbf=0, mttr=0 ):
    
    dev = create_ict_device(ict_net, name=name, type=devtype, in_service=in_service, use_uuid=use_uuid, uid=uid, mtbf=mtbf, mttr=mttr)
    app = create_ict_app(ict_net, name=name, type=apptype, in_service=in_service, use_uuid=use_uuid, uid=uid, conversions=conversions, device=dev)
    return (dev, app)


def create_ict_connection(ict_net, name=None, index=None, in_service=True, use_uuid=False, uid=None,
                          from_app=None, to_app=None, protocol=None, info_items=None, peers=None, producer=None, prod_freq_ms=None):    
        
    if index is not None and index in ict_net["conn"].index:
        raise UserWarning("A connection with index %s already exists" % index)

    if index is None:
        index = get_free_id(ict_net["conn"])
        
    if peers:
        if not (peers[0][0]=='device' and peers[1][0]=='device'): 
            raise UserWarning("Wrong parameter for peers (must be device elements)")
            return 

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
        if peers is not None:
            pdev1 = uuid2elt(ict_net, peers[0])[1]  # TODO add element type check
            pdev2 = uuid2elt(ict_net, peers[1])[1]  # TODO add element type check
            pe = tuple2str( (pdev1, pdev2) )
        else:
            pe = None        
        from_app = uuid2elt(ict_net, from_app)[1] # TODO add element type check
        to_app   = uuid2elt(ict_net, to_app)[1]   # TODO add element type check
    else: 
        ruuid = None
        if peers is not None: 
            pe = tuple2str((peers[0][1], peers[1][1]))
        else:
            pe = None
        from_app = from_app[1] # TODO add element type check
        to_app   = to_app[1]   # TODO add element type check
            
    # TODO: check if from_app == to_app    
    ict_net.conn.loc[index, ["name", "in_service", "from", "to", "protocol", "info_items", 
                             "peers", "producer", "prod_freq_ms", "uuid" ]] = [name, in_service, from_app, to_app, protocol, ii, 
                              pe, pr, pf, ruuid]
    

    _preserve_dtypes(ict_net.conn, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('conn', index)


def check_net(ict_net):
    return