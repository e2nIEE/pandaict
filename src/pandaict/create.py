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
from enums import InfoItem, NodeType, DeviceType, AppType

import logging
logger = logging.getLogger("pandaICT_Core")

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

def create_ict_node(ict_net, name=None, node_type=None, index=None, in_service=True, use_uuid=False, uid=None, 
                     geodata=None, link_types=None, ber=0, mtbf_h=0, mttr_h=0):
    
    if ict_net is None:
        raise UserWarning("ict_net must not be None")
    if node_type is not None and not isinstance(node_type, NodeType):
        raise UserWarning("node_type must be NodeType")    
    if index is not None and index in ict_net["node"].index:
        raise UserWarning("A node with index %s already exists" % index)
    if geodata is not None:
        if not isinstance(geodata, tuple) or len(geodata) != 2:
            raise UserWarning("geodata must be given as (x, y) tuple")
    if link_types is not None: 
        if isinstance(link_types, list):
            for lt in link_types: 
                if not lt in ict_net.std_types['link'].keys():
                    raise UserWarning("link_type "+str(lt)+" not found in std_types")
        elif not link_types in ict_net.std_types['link'].keys():
            raise UserWarning("link_type "+str(link_types)+" not found in std_types")
    if uid is not None: 
            if not isinstance(uid, uuid.UUID) and not isinstance(uid, str):
                raise UserWarning("uid must be None, uuid4 or string")                        
            try:
                uelt = uuid2elt(ict_net, uuid.UUID(str(uid)))
            except:
                raise UserWarning("uid '"+str(uid)+"' can not be converted to UUID object")  
            if uelt is not None:
                raise UserWarning("uid already in use for "+str(uuid2elt(ict_net, uuid.UUID(str(uid))))) 
            
    if index is None:
        index = get_free_id(ict_net["node"])

    dtypes = ict_net.node.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    if isinstance(link_types, list):
        lt = list2str(link_types)
    elif link_types is not None:
        lt = str(link_types) 
    else:
        lt = 'all'
        
    if geodata is not None:
        gd = tuple2str(geodata)
    else:
        gd = None
           
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uuid.UUID(str(uid))
    else: 
        ruuid = None
    ict_net.node.loc[index, ["name", "type", "in_service", "geodata", "link_types", "ber", "mtbf_h", "mttr_h", "uuid"]] = [name, node_type, in_service, gd, lt, ber, mtbf_h, mttr_h, ruuid]

    _preserve_dtypes(ict_net.node, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('node', index)

    
def create_ict_link(ict_net, from_elt, to_elt, name=None, link_type=None, index=None, in_service=True, use_uuid=False, uid=None,
                    protocols=None, length_km=0 ):
    if ict_net is None:
        raise UserWarning("ict_net must not be None")
    if use_uuid: 
        if from_elt is None or not isinstance(from_elt, uuid.UUID):
            raise UserWarning("from_elt must be uuid4")
        if to_elt is None or not (isinstance(to_elt, uuid.UUID) or isinstance(to_elt, list)):
            raise UserWarning("to_elt must be uuid4 or list of uuid4")
        if isinstance(to_elt, list):
            for i in range(0, len(to_elt)):
                if not isinstance(to_elt[i], uuid.UUID): 
                    raise UserWarning("to_elt["+str(i)+"] must be uuid4") 
        if from_elt==to_elt: 
            raise UserWarning("from_elt and to_elt must not be equal") 
        if uid is not None: 
            if not isinstance(uid, uuid.UUID) and not isinstance(uid, str):
                raise UserWarning("uid must be None, uuid4 or string")            
            if str(from_elt)==str(uid): 
                raise UserWarning("from_elt and uid must not be equal") 
            if str(to_elt)==str(uid): 
                raise UserWarning("to_elt and uid must not be equal") 
            try:
                uelt = uuid2elt(ict_net, uuid.UUID(str(uid)))
            except:
                raise UserWarning("uid '"+str(uid)+"' can not be converted to UUID object")   
            if uelt is not None:
                raise UserWarning("uid already in use for "+str(uuid2elt(ict_net, uuid.UUID(str(uid))))) 
    else:        
        if not isinstance(from_elt, tuple):
            raise UserWarning("from_elt must be (str, int) tuple")     
        if not (from_elt[0]=='device' or from_elt[0]=='node'):
            raise UserWarning("from_elt is "+str(from_elt[0])+", must be dev or node") 
        if (not isinstance(to_elt, tuple) and not isinstance(to_elt, list)):
            raise UserWarning("to_elt must be (str, int) tuple or list of such tuples")  
        if isinstance(to_elt, tuple):
            if not (to_elt[0]=='device' or to_elt[0]=='node'):
                raise UserWarning("to_elt is "+str(to_elt[0])+", must be dev or node") 
        else:            
            for i in range(0, len(to_elt)):
                if not isinstance(to_elt[i], tuple):
                    raise UserWarning("to_elt must be (str, int) tuple or list of such tuples") 
                if not (to_elt[i][0]=='device' or to_elt[i][0]=='node'):
                    raise UserWarning("to_elt["+str(i)+"] is "+str(to_elt[i][0])+", must be dev or node")   
        
    if link_type is not None:
        if not isinstance(link_type, str):
            raise UserWarning("link_type must be str") 
        elif not link_type in ict_net.std_types['link'].keys():
            raise UserWarning("link_type "+str(link_type)+" not found in std_types") 
    if index is not None and index in ict_net["link"].index:
        raise UserWarning("A link with index %s already exists" % index)  
    if protocols is not None: 
        if isinstance(protocols, list):
            for pr in protocols: 
                if not pr in ict_net.std_types['protocol'].keys():
                    raise UserWarning("protocol "+str(pr)+" not found in std_types")
        elif not protocols in ict_net.std_types['protocol'].keys():
            raise UserWarning("protocol "+str(protocols)+" not found in std_types")

    if index is None:
        index = get_free_id(ict_net["link"])

    dtypes = ict_net.link.dtypes
    
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0    
    if (use_uuid):         
        if uid is None:
            ruuid = uuid.uuid4()
        else:        
            ruuid = uuid.UUID(str(uid))
        from_elt = uuid2elt(ict_net, from_elt)
        if from_elt is None:
            raise UserWarning("from_elt not found by uuid") 
        if not (from_elt[0]=='device' or from_elt[0]=='node'):
            raise UserWarning("from_elt is "+str(from_elt[0])+", must be device or node") 
        from_elt = tuple2str(from_elt) 
        if isinstance(to_elt, list):
            h = [tuple2str(uuid2elt(ict_net, uid)) for uid in to_elt]
            if h is None or None in h:                
                raise UserWarning("at least one to_elt not found by uuid")
            if not all(('device' in e or 'node' in e) for e in h):
                raise UserWarning("all to_elt must be device or node") 
            to_elt = list2str(h)
        else:
            to_elt = uuid2elt(ict_net, to_elt)
            if to_elt is None:                
                raise UserWarning("to_elt not found by uuid")
            if not (to_elt[0]=='device' or to_elt[0]=='node'):
                raise UserWarning("to_elt is "+str(to_elt[0])+", must be device or node")                  
            to_elt = tuple2str(to_elt)
            
    else: 
        ruuid = None  
        from_elt = tuple2str(from_elt)
        if isinstance(to_elt, list):
            h = [tuple2str(elt) for elt in to_elt]
            to_elt = list2str(h)
        else:
            to_elt = tuple2str(to_elt)
          
    if from_elt==to_elt: 
        raise UserWarning("from_elt and to_elt must not be equal") 
    if from_elt in to_elt:
        raise UserWarning("to_elt must not contain from_elt") 
        
    if isinstance(protocols, list):
        pr = list2str(protocols)
    elif protocols is not None:
        pr = str(protocols) 
    else:
        pr = None    
    
    ict_net.link.loc[index, ["name", "type", "in_service", "from", "to", "protocols", "length_km", "uuid"]] = [name, link_type, in_service, from_elt, to_elt, pr, length_km, ruuid]

    _preserve_dtypes(ict_net.link, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('link', index)


def create_ict_device(ict_net, name=None, device_type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      mtbf=0, mttr=0 ):
    
    if ict_net is None:
        raise UserWarning("ict_net must not be None")
    if device_type is not None and not isinstance(device_type, DeviceType):
        raise UserWarning("device_type must be DeviceType")    
    if index is not None and index in ict_net["device"].index:
        raise UserWarning("A device with index %s already exists" % index)        
    if uid is not None: 
        if not isinstance(uid, uuid.UUID) and not isinstance(uid, str):
            raise UserWarning("uid must be None, uuid4 or string")                        
        try:
            uelt = uuid2elt(ict_net, uuid.UUID(str(uid)))
        except:
            raise UserWarning("uid '"+str(uid)+"' can not be converted to UUID object") 
        if uelt is not None:
            raise UserWarning("uid already in use for "+str(uuid2elt(ict_net, uuid.UUID(str(uid)))))  

    if index is None:
        index = get_free_id(ict_net["device"])

    dtypes = ict_net.device.dtypes
           
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uuid.UUID(str(uid))
    else: 
        ruuid = None
        
    ict_net.device.loc[index, ["name", "type", "in_service", "mtbf", "mttr", "uuid" ]] = [name, device_type, in_service, mtbf, mttr, ruuid]

    _preserve_dtypes(ict_net.device, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('device', index)
    
    
def create_ict_app(ict_net, name=None, app_type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      conversions=None, device=None ):
    
    if ict_net is None:
        raise UserWarning("ict_net must not be None")
    if app_type is not None and not isinstance(app_type, AppType):
        raise UserWarning("app_type must be AppType")    
    if index is not None and index in ict_net["app"].index:
        raise UserWarning("An app with index %s already exists" % index)        
    if uid is not None: 
        if not isinstance(uid, uuid.UUID) and not isinstance(uid, str):
            raise UserWarning("uid must be None, uuid4 or string")                        
        try:
            uelt = uuid2elt(ict_net, uuid.UUID(str(uid)))
        except:
            raise UserWarning("uid '"+str(uid)+"' can not be converted to UUID object") 
        if uelt is not None:
            raise UserWarning("uid already in use for "+str(uuid2elt(ict_net, uuid.UUID(str(uid)))))  
    if device is None:
        raise UserWarning("device must not be None")
    if conversions is not None:
        if not isinstance(conversions, list):
            raise UserWarning("conversions must be given as list")
        for cn in conversions: 
            if not isinstance(cn, tuple): 
                raise UserWarning("conversions list items for app '"+str(name)+"' must be tuples (String, String, Float, Float)")
            if len(cn)<2: 
                raise UserWarning("conversions list items for app '"+str(name)+"' must have at least two entries")
            if cn[0]==cn[1]:
                raise UserWarning("conversion for app  '"+str(name)+"' must not convert between same protocols")
            if cn[0] not in ict_net.std_types['protocol'].keys():
                raise UserWarning("conversion protocol '"+str(cn[0])+"' for app  '"+str(name)+"' not found in std_types")
            if cn[1] not in ict_net.std_types['protocol'].keys():
                raise UserWarning("conversion protocol '"+str(cn[1])+"' for app  '"+str(name)+"' not found in std_types")
                
    if index is None:
        index = get_free_id(ict_net["app"])

    dtypes = ict_net.app.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0        
    if conversions is not None:
        cn = list2str(conversions)
    else:
        cn = None
        
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uuid.UUID(str(uid))
        rdevice = uuid2elt(ict_net, device) 
        if rdevice is None:
            raise UserWarning("device not found by uuid") 
        if not rdevice[0]=='device': 
            raise UserWarning("device parameter is "+str(rdevice[0])+", must be device")
        rdevice = rdevice[1]
    else: 
        ruuid = None
        if not device[0]=='device': 
            raise UserWarning("device parameter is "+str(device[0])+", must be device")  
        rdevice = device[1]
        
    ict_net.app.loc[index, ["name", "type", "in_service", "conversions", "uuid", "device" ]] = [name, app_type, in_service, cn, ruuid, rdevice]

    _preserve_dtypes(ict_net.app, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('app', index)


def create_ict_devapp(ict_net, name=None, device_type=None, app_type=None, in_service=True, use_uuid=False,            
                      conversions=None, mtbf=0, mttr=0 ):
    
    dev = create_ict_device(ict_net, name=name, device_type=device_type, in_service=in_service, use_uuid=use_uuid, mtbf=mtbf, mttr=mttr)    
    app = create_ict_app(ict_net, name=name, app_type=app_type, in_service=in_service, use_uuid=use_uuid, conversions=conversions, device=dev)
    return (dev, app)


def create_ict_connection(ict_net, name=None, index=None, in_service=True, use_uuid=False, uid=None,
                          from_app=None, to_app=None, protocol=None, info_items=None, peers=None, producer=None, prod_freq_ms=None):    
        
    
    if ict_net is None:
        raise UserWarning("ict_net must not be None")
    if peers is not None and (not isinstance(peers, tuple) or not len(peers)==2):
        raise UserWarning("peers must be a 2-tuple")
    if peers is not None and peers[0]==peers[1]:
        raise UserWarning("peers must not be equal") 
    if use_uuid: 
        if from_app is None or not isinstance(from_app, uuid.UUID):
            raise UserWarning("from_app must be uuid4")
        if to_app is None or not isinstance(to_app, uuid.UUID):
            raise UserWarning("to_app must be uuid4")
        if from_app==to_app: 
            raise UserWarning("from_app and to_app must not be equal") 
        if peers is not None and (not isinstance(peers[0], uuid.UUID) or not isinstance(peers[1], uuid.UUID)):
            raise UserWarning("peers must be uuid4")
        if uid is not None: 
            if not isinstance(uid, uuid.UUID) and not isinstance(uid, str):
                raise UserWarning("uid must be None, uuid4 or string")            
            if str(from_app)==str(uid): 
                raise UserWarning("from_app and uid must not be equal") 
            if str(to_app)==str(uid): 
                raise UserWarning("to_app and uid must not be equal") 
            try:
                uelt = uuid2elt(ict_net, uuid.UUID(str(uid)))
            except:
                raise UserWarning("uid '"+str(uid)+"' can not be converted to UUID object")   
            if uelt is not None:
                raise UserWarning("uid already in use for "+str(uuid2elt(ict_net, uuid.UUID(str(uid))))) 
    else:        
        if not isinstance(from_app, tuple):
            raise UserWarning("from_app must be (str, int) tuple")      
        if not (from_app[0]=='app'):
            raise UserWarning("from_app is "+str(from_app[0])+", must be app") 
        if not isinstance(to_app, tuple):
            raise UserWarning("to_app must be (str, int) tuple")    
        if not (to_app[0]=='app'):
            raise UserWarning("to_app is "+str(to_app[0])+", must be app") 
        if peers is not None:
            if not isinstance(peers[0], tuple) or not isinstance(peers[1], tuple):
                raise UserWarning("peers elements must be tuples (str, int)")
            if not (peers[0][0]=='app' and peers[1][0]=='app'):
                raise UserWarning("peers elements must be app-type")
               
    if index is not None and index in ict_net["conn"].index:
        raise UserWarning("A connection with index %s already exists" % index)  
    if protocol is not None: 
        if not protocol in ict_net.std_types['protocol'].keys():
            raise UserWarning("protocol "+str(protocol)+" not found in std_types")
    if info_items is not None:
        if not isinstance(info_items, list):
            raise UserWarning("info_items must be a list of InfoItem") 
        for ii in info_items: 
            if not isinstance(ii, InfoItem):
                raise UserWarning("info_items must be a list of InfoItem")
    if producer is not None:
        if not isinstance(producer, list):
            raise UserWarning("producer must be None or list")
        if len(producer)!=len(info_items) or not all((p == "0" or p == "1") for p in producer):
            raise UserWarning("producer length must be the same as info_items, and all entries must be 0 or 1")
    if prod_freq_ms is not None:
        if not isinstance(prod_freq_ms, list):
            raise UserWarning("prod_freq_ms must be None or list")
        if len(prod_freq_ms)!=len(info_items) or not all((isinstance(p, float) for p in prod_freq_ms)):
            raise UserWarning("prod_freq_ms length must be the same as info_items, and all entries must be float.")

    if index is None:
        index = get_free_id(ict_net["conn"])
        
    dtypes = ict_net.conn.dtypes
    # NOTE: lists need to be converted to str because pandas dataframes can not use lists for pandas < 2.0.0
    # but current pandapower release won't work with pandas >= 2.0.0
    if info_items is not None: 
        ii = list2str(info_items)
    else:
        ii = None    
    if producer is not None:
        pr = list2str(producer)
    else:
        pr = None 
    if prod_freq_ms is not None:
        pf = list2str(prod_freq_ms)            
    else:
        pf = None
        
    if (use_uuid): 
        if uid is None:
            ruuid = uuid.uuid4()
        else:
            ruuid = uuid.UUID(str(uid))
        if peers is not None:
            pdev1 = uuid2elt(ict_net, peers[0])  
            if pdev1 is None:                
                raise UserWarning("pdev1 not found by uuid") 
            if not (pdev1[0]=='app'):
                raise UserWarning("pdev1 is "+str(pdev1[0])+", must be app")         
            pdev2 = uuid2elt(ict_net, peers[1])
            if pdev2 is None:                
                raise UserWarning("pdev2 not found by uuid") 
            if not (pdev2[0]=='app'):
                raise UserWarning("pdev2 is "+str(pdev2[0])+", must be app")                     
            pe = tuple2str( (pdev1[1], pdev2[1]) )
        else:
            pe = None        
        from_app = uuid2elt(ict_net, from_app) 
        if from_app is None:                
                raise UserWarning("from_app not found by uuid")
        if not (from_app[0]=='app'):
            raise UserWarning("from_app is "+str(from_app[0])+", must be app")
        from_app = from_app[1]
        to_app   = uuid2elt(ict_net, to_app)
        if to_app is None:                
            raise UserWarning("to_app not found by uuid")
        if not (to_app[0]=='app'):
            raise UserWarning("to_app is "+str(to_app[0])+", must be app")
        to_app = to_app[1]
    else: 
        ruuid = None
        if peers is not None: 
            pe = tuple2str((peers[0][1], peers[1][1]))
        else:
            pe = None
        from_app = from_app[1] # elt type already checked above
        to_app   = to_app[1]   # elt type already checked above
        
    if from_app==to_app: 
        raise UserWarning("from_app and to_app must not be equal") 
            
    ict_net.conn.loc[index, ["name", "in_service", "from", "to", "protocol", "info_items", 
                             "peers", "producer", "prod_freq_ms", "uuid" ]] = [name, in_service, from_app, to_app, protocol, ii, 
                              pe, pr, pf, ruuid]
    

    _preserve_dtypes(ict_net.conn, dtypes)

    if use_uuid:
        return ruuid
    else:
        return ('conn', index)

