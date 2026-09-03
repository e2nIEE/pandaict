'''
Created on 30.01.2024
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

from pandaict.auxiliary import pandaICTNet
from pandaict.auxiliary import ADict, __get_free_id, __preserve_dtypes
from pandaict.create_empty_net import create_empty_network
from pandaict.utils.utils import uuid2elt, elt2uuid, check_all_uuid, get_elts_any
from pandaict.utils.enums import InfoItem, NodeType, DeviceType, AppType
from pandaict.pilogger import pilogger
import numbers
import uuid


def __create_ruuid(uid, use_uuid):
    
    if (use_uuid):
        ruuid = uuid.uuid4() if uid is None else uuid.UUID(str(uid))
    else:
        ruuid = None
    return ruuid

def __create_net_index_check(ict_net, index, elttype):
    
    if ict_net is None:
        raise UserWarning("ict_net must not be None")
    if index is not None and index in ict_net[elttype].index:
        raise UserWarning("A "+str(elttype)+" with index %s already exists" % index)

def __create_std_type_check(ict_net, std_type_elt, allowed_dtypes, expected_elt_type, allow_list=False):
    
    if std_type_elt is not None:        
        if (not allow_list and isinstance(std_type_elt, (list, tuple))):
            raise UserWarning("std type element must not be list")
        lste = std_type_elt if isinstance(std_type_elt, (list, tuple)) else [std_type_elt]
        for ste in lste:   
            if not isinstance(ste, allowed_dtypes):
                raise UserWarning("std type element must be one of "+str(allowed_dtypes)) 
            if ste not in ict_net.std_types[expected_elt_type].keys():
                raise UserWarning("std type element "+str(ste)+" not found in "+str(expected_elt_type)+" std_types")
        
def __check_uuid(ict_net, uid):
    if uid is not None:
        if not isinstance(uid, uuid.UUID) and not isinstance(uid, str):
            raise UserWarning("uid must be None, uuid4 or string")
        try:
            uelt = uuid2elt(ict_net, uuid.UUID(str(uid)))
        except ValueError:
            raise UserWarning("uid '" + str(uid) + "' can not be converted to UUID object")       
        if uelt is not None:
            raise UserWarning("uid already in use for " + str(uuid2elt(ict_net, uuid.UUID(str(uid)))))
        
def __check_list_items(clist, allowed_length=None, allowed_types=None, allowed_values=None):    
    
    if clist is None:
        return 
    if not isinstance(clist, list):
        raise UserWarning("parameter must be a list")
    if allowed_length is not None and len(clist)!=allowed_length:
        raise UserWarning("parameter must be a list with length "+str(allowed_length))
    for cl in clist:
        if allowed_types is not None and not isinstance(cl, allowed_types):
            raise UserWarning("parameter list must only contain elements of types "+str(allowed_types))
        if allowed_values is not None and cl not in allowed_values:
            raise UserWarning("parameter list elements must only have values "+str(allowed_values))

def __check_elt_list_and_get_index(pi_elts, paramname, expected_types):
    for pe in pi_elts:
        if not isinstance(pe, tuple) or not isinstance(pe[0],str) or not isinstance(pe[1], numbers.Integral):
            raise UserWarning("all items in "+paramname+" must be (str, int) tuples") 
        if expected_types is not None and pe[0] not in expected_types:
            raise UserWarning("an item in "+paramname+" is "+str(pe[0])+", must be one of "+str(expected_types))
    return pi_elts[0][1] 

def __check_elts_and_get_index(pi_elts, paramname, expected_types=None, allow_list=True):
    if pi_elts is None:
        raise UserWarning(str(expected_types)+" not found") 
    elif isinstance(pi_elts, list) and allow_list:             
        return __check_elt_list_and_get_index(pi_elts, paramname, expected_types)         
    elif isinstance(pi_elts, tuple):                
        if pi_elts[0] not in expected_types: 
            raise UserWarning(str(paramname)+" parameter is "+str(pi_elts[0])+", must be one of "+str(expected_types))
        return pi_elts[1]
    else:
        if allow_list:
            raise UserWarning(str(paramname)+" must be (str, int) tuple or list of such tuples")
        else:
            raise UserWarning(str(paramname)+" must be (str, int) tuple")
        
def __create_ict_node_check__(ict_net, node_type, index, uid, geodata, link_types):
    
    __create_net_index_check(ict_net, index, "node")
    if node_type is not None and not isinstance(node_type, NodeType):
        raise UserWarning("node_type must be NodeType")
    if geodata is not None:
        if isinstance(geodata, dict):
            if "type" not in geodata.keys() or "coordinates" not in geodata.keys():
                raise UserWarning("geodata must contain 'type' and 'coordinates' keys") 
        elif not isinstance(geodata, tuple) or len(geodata) != 2 or not isinstance(geodata[0], float) or not isinstance(geodata[0], float):
            raise UserWarning("geodata must be (float, float) tuple or geojson")
    __create_std_type_check(ict_net, link_types, (str), 'link', allow_list=True)
    __check_uuid(ict_net, uid) 

def create_ict_node(ict_net, name=None, node_type=None, index=None, in_service=True, use_uuid=False, uid=None, 
                     geodata=None, link_types=None, ber=0, mtbf_h=0, mttr_h=0):
    """
    Adds one node in table ict_net["node"].

    Nodes are network elements that can support connection of different physical links, and route data on ISO/OSI layers 1-3.

    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which the node is created    

    :OPTIONAL:
        **name** (string, default None) - the name for this node

        **node_type** (aenum, default None) - the node type. Use an NODE_TYPE aenum. 
        
        **index** (int, default None) - Force a specified list index if it is available. If None, the \
            index one higher than the highest already existing index is selected.

        **in_service** (boolean, default True) - True if node is in service, False if out of service

        **use_uuid** (boolean, default False) - Set True if uuids shall be used. If False, pandaict element notation is used. 
        
        **uid** (UUID4 or string, default None) - user-selected uuid for this node (must not be used in this network yet)
        
        **geodata** ((x,y)-tuple or GeoJSON Point, default None) - coordinates used for plotting
        
        **link_types** (aenum, default None) - link types supported by the node. Standard link types can be used. \
            None means that all link types are supported.
       
        **ber** (float, 0) - Bit error rate for this node, in p.u.

        **mtbf_h** (float, 0) - Mean time before failure for this node, in hours. Zero means not defined.
        
        **mttr_h** (float, 0) - Mean time to repair for this node, in hours. Zero means not defined.

    :OUTPUT:
        **elt** ((str,int) or UUID4) - The unique ID of the created element. If use_uuid==False, pandaict element notation is used, \
            otherwise a uuid is returned (either the user selected uid or a newly generated one)

    :EXAMPLE:
        create_ict_node(net, name = "Node1")
    """
    
    __create_ict_node_check__(ict_net, node_type, index, uid, geodata, link_types)

    dtypes = ict_net.node.dtypes
    if index is None:
        index = __get_free_id(ict_net["node"])
    ruuid = __create_ruuid(uid, use_uuid)
        
    ict_net.node.loc[index, ["name", "type", "in_service", "ber", "mtbf_h", "mttr_h", "uuid"]] = [name, node_type, in_service, ber, mtbf_h, mttr_h, ruuid]
    ict_net.node.at[index,'geodata'] = geodata
    ict_net.node.at[index,'link_types'] = link_types or 'all'

    __preserve_dtypes(ict_net.node, dtypes)
    
    return ruuid if use_uuid else ('node', int(index))

def __create_ict_link_check_uuid(ict_net, from_elt, to_elt, uid):
    
    check_all_uuid(from_elt)
    check_all_uuid(to_elt)        
    if from_elt == to_elt:
        raise UserWarning("from_elt and to_elt must not be equal")        
    __check_uuid(ict_net, uid)
    if uid is not None:
        if str(from_elt) == str(uid): 
            raise UserWarning("from_elt and uid must not be equal")
        if str(to_elt) == str(uid):         
            raise UserWarning("to_elt must not equal uid")
        if any(str(to_elt) == str(uid)):         
            raise UserWarning("to_elt must not contain uid")            
                
def __create_ict_link_check_nouuid(from_elt, to_elt):
        
    __check_elts_and_get_index(from_elt, 'from_elt', ['device','node'])  
    __check_elts_and_get_index(to_elt, 'to_elt', ['device','node'])    

def create_ict_link(ict_net, from_elt, to_elt, name=None, link_type=None, index=None, in_service=True, use_uuid=False, uid=None,
                    length_km=0 ):
    
    """
    Adds one link in table ict_net["link"].

    Links represent physical point-to-point ICT connections from device to node or in-between nodes. 

    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which the link is created    

        **from_elt** ((string,int) or UUID4) - Link start element, in pandaict element notation if use_uuid == False, \
            else as UUID. Element type must be device or node.     
        
        **to_elt** ((string,int) or UUID4 or list of such) - Link end element or list of elements in pandaict element notation if use_uuid == False, \
            else as UUID. Element type must be device or node. 
        
    :OPTIONAL:
        **name** (string, default None) - the name for this link.

        **link_type** (string, default None) - the link type. Standard link type can be used.  
        
        **index** (int, default None) - Force a specified list index if it is available. If None, the \
            index one higher than the highest already existing index is selected.

        **in_service** (boolean, default True) - True for in service or False for out of service.

        **use_uuid** (boolean, default False) - True if uuids shall be used; if False, pandaict element notation is used. 
        
        **uid** (UUID4 or string, default None) - user-selected uuid for this link (must not be used in this network yet).
        
        **length_km** (float, default 0) - Link line length for wired link type, or air distance for wireless link types.
            
    :OUTPUT:
        **elt** ((string,int) or UUID4) - The unique ID of the created element. If use_uuid==False, pandaict element notation is used, \
            otherwise a uuid is returned (either the user selected uid or a newly generated one).

    :EXAMPLE:
        create_ict_link(net, from_elt = ("node", 1), to_elt = ("device", 3), link_type="Binary")    
    """
    
    __create_net_index_check(ict_net, index, "link")    
    if use_uuid:
        __create_ict_link_check_uuid(ict_net, from_elt, to_elt, uid)
    else:                     
        __create_ict_link_check_nouuid(from_elt, to_elt)
    __create_std_type_check(ict_net, link_type, (str), 'link')
    
    if index is None:
        index = __get_free_id(ict_net["link"])
    dtypes = ict_net.link.dtypes        
    ruuid = __create_ruuid(uid, use_uuid)
    
    if not isinstance(to_elt, list):
        to_elt = [to_elt]
    
    if (use_uuid):                 
        from_elt = get_elts_any(ict_net, from_elt, expected=['device','node'])        
        to_elt = get_elts_any(ict_net, to_elt, expected=['device','node'])                          
        
    if from_elt==to_elt: 
        raise UserWarning("from_elt and to_elt must not be equal") 
    if from_elt in to_elt:
        raise UserWarning("to_elt must not contain from_elt")
            
    ict_net.link.loc[index, ["name", "type", "in_service", "length_km", "uuid"]] = [name, link_type, in_service, length_km, ruuid]
    ict_net.link.at[index,'from'] = from_elt
    ict_net.link.at[index,'to'] = to_elt

    __preserve_dtypes(ict_net.link, dtypes)

    return ruuid if use_uuid else ('link', int(index))

def __create_device_check(ict_net, device_type, uid):
    
    if device_type is not None and not isinstance(device_type, DeviceType):
        raise UserWarning("device_type must be DeviceType")
    __check_uuid(ict_net, uid)

def create_ict_device(ict_net, name=None, device_type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      mtbf_h=0, mttr_h=0 ):
    
    """
    Adds one device in table ict_net["device"].

    Devices are physical communication endpoints. A device is connected to one or more node(s) by links, and is running one or more Apps.  
    A Converter is a special type of device, running apps which convert between different protocols (ISO/OSI level >=4). 
    
    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which the device is created.    

    :OPTIONAL:
        **name** (string, default None) - the name for this device.

        **device_type** (aenum, default None) - the device type. Use a DEVICE_TYPE aenum. 
        
        **index** (int, default None) - Force a specified list index if it is available. If None, the \
            index one higher than the highest already existing index is selected.

        **in_service** (boolean, default True) - True for in service or False for out of service

        **use_uuid** (boolean, default False) - True if uuids shall be used; if False, pandaict element notation is used 
        
        **uid** (UUID4 or string, default None) - user-selected uuid for this device (must not be used in this network yet)            
        
        **mtbf_h** (float, 0) - Mean time before failure for this device, in hours. Zero means not defined.
        
        **mttr_h** (float, 0) - Mean time to repair for this device, in hours. Zero means not defined.

    :OUTPUT:
        **elt** ((str,int) or UUID4) - The unique ID of the created element. If use_uuid==False, pandaict element notation is used, \
            otherwise a uuid is returned (either the user selected uid or a newly generated one)

    :EXAMPLE:
        create_ict_device(net, name = "PowerMeter1")
    """
    
    __create_net_index_check(ict_net, index, "device")    
    __create_device_check(ict_net, device_type, uid)  

    if index is None:
        index = __get_free_id(ict_net["device"])
    dtypes = ict_net.device.dtypes        
    ruuid = __create_ruuid(uid, use_uuid)
        
    ict_net.device.loc[index, ["name", "type", "in_service", "mtbf_h", "mttr_h", "uuid" ]] = [name, device_type, in_service, mtbf_h, mttr_h, ruuid]

    __preserve_dtypes(ict_net.device, dtypes)

    return ruuid if use_uuid else ('device', int(index))
     
def __create_app_check_conversion(ict_net, cn, name):
    if not isinstance(cn, tuple):
        raise UserWarning("conversions list items for app '" + str(name) + "' must be tuples (String, String, Float, Float)")
    if len(cn) < 2:
        raise UserWarning("conversions list items for app '" + str(name) + "' must have at least two entries")
    if cn[0] == cn[1]:
        raise UserWarning("conversion for app  '" + str(name) + "' must not convert between same protocols")
    if cn[0] not in ict_net.std_types['protocol'].keys():
        raise UserWarning("conversion protocol '" + str(cn[0]) + "' for app  '" + str(name) + "' not found in std_types")
    if cn[1] not in ict_net.std_types['protocol'].keys():
        raise UserWarning("conversion protocol '" + str(cn[1]) + "' for app  '" + str(name) + "' not found in std_types")

def __create_app_check(ict_net, name, app_type, uid, conversions, device):
    
    if app_type is not None and not isinstance(app_type, AppType):
        raise UserWarning("app_type must be AppType")
    __check_uuid(ict_net, uid)
    if device is None:
        raise UserWarning("device must not be None")
    if conversions is not None:
        if not isinstance(conversions, list):
            raise UserWarning("conversions must be given as list")
        for cn in conversions:
            __create_app_check_conversion(ict_net, cn, name)
        
def create_ict_app(ict_net, name=None, app_type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      conversions=None, device=None ):
    
    """
    Adds one app in table ict_net["app"].

    Apps are end-to-end communication endpoints. Each app runs on exactly one device. Apps are connected by connections
    for transmission of information items. A special type of app is the Converter app, which translates between different protocols
    and must run on a Converter-type device.  
    
    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which the app is created.
        
        **device** (int, default None) - Index in device table, referencing the device this app runs on.    

    :OPTIONAL:
        **name** (string, default None) - the name for this app.

        **app_type** (aenum, default None) - the app type. Use an APP_TYPE aenum. 
        
        **index** (int, default None) - Force a specified list index if it is available. If None, the \
            index one higher than the highest already existing index is selected.

        **in_service** (boolean, default True) - True for in service or False for out of service.

        **use_uuid** (boolean, default False) - True if uuids shall be used; if False, pandaict element notation is used. 
        
        **uid** (UUID4 or string, default None) - user-selected uuid for this app (must not be used in this network yet).            
        
        **conversions** (list of (string,string) tuple, default None) - List of protocol pairs the app is converting between \
            (Only for Converter type app).
                

    :OUTPUT:
        **elt** ((str,int) or UUID4) - The unique ID of the created element. If use_uuid==False, pandaict element notation is used, \
            otherwise a uuid is returned (either the user selected uid or a newly generated one).

    :EXAMPLE:
        create_ict_app(net, name = "PowerMeterApp1", device=0)
    """
        
    __create_net_index_check(ict_net, index, "app")    
    __create_app_check(ict_net, name, app_type, uid, conversions, device)
                
    if index is None:
        index = __get_free_id(ict_net["app"])
    dtypes = ict_net.app.dtypes
    ruuid = __create_ruuid(uid, use_uuid)
    
    if (use_uuid):            
        rdevice = __check_elts_and_get_index(uuid2elt(ict_net, device), 'device', 'device')
    else:
        rdevice = __check_elts_and_get_index(device, 'device', 'device')            
        
    ict_net.app.loc[index, ["name", "type", "in_service", "uuid", "device" ]] = [name, app_type, in_service, ruuid, rdevice]
    ict_net.app.at[index, "conversions"] = conversions

    __preserve_dtypes(ict_net.app, dtypes)

    return ruuid if use_uuid else ('app', int(index))

def create_ict_devapp(ict_net, name=None, device_type=None, app_type=None, in_service=True, use_uuid=False,            
                      conversions=None, mtbf_h=0, mttr_h=0 ):
    
    """
    Adds one device in table ict_net["device"] and one app in table ict_net["app"]. The app is set to run on the device.

    This function is particularly useful to model a device (physical communication endpoint) that runs exactly one app (application level communication endpoint). 
    This includes e.g. substation control elements or stand-alone protocol converters.
    
    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which device and app are created.    

    :OPTIONAL:
        **name** (string, default None) - name used for both device and app.

        **device_type** (aenum, default None) - the device type. Use a DEVICE_TYPE aenum.

        **app_type** (aenum, default None) - the app type. Use an APP_TYPE aenum. 
                
        **in_service** (boolean, default True) - True for in service or False for out of service.

        **use_uuid** (boolean, default False) - True if uuids shall be used; if False, pandaict element notation is used.            
        
        **conversions** (list of (string,string) tuple, default None) - List of protocol pairs the app is converting between \
            (Only for Converter type app).
        
        **mtbf_h** (float, 0) - Mean time before failure for device, in hours. Zero means not defined.
        
        **mttr_h** (float, 0) - Mean time to repair for device, in hours. Zero means not defined.

    :OUTPUT:
        **elt** (List of (str,int) or UUID4) - List of device and app identifiers of the created elements. If use_uuid==False, pandaict element \
            notation is used, otherwise uuids are returned.

    :EXAMPLE:
        create_ict_devapp(net, name = "PowerMeter1")
    """
    
    dev = create_ict_device(ict_net, name=name, device_type=device_type, in_service=in_service, use_uuid=use_uuid, mtbf_h=mtbf_h, mttr_h=mttr_h)    
    app = create_ict_app(ict_net, name=name, app_type=app_type, in_service=in_service, use_uuid=use_uuid, conversions=conversions, device=dev)
    return (dev, app)

def __create_connection_check_uuid(ict_net, uid, from_app, to_app, peers):
    check_all_uuid(from_app)
    check_all_uuid(to_app, False)    
    if from_app == to_app:
        raise UserWarning("from_app and to_app must not be equal")
    if peers is not None and (not isinstance(peers[0], uuid.UUID) or not isinstance(peers[1], uuid.UUID)):
        raise UserWarning("peers must be uuid4")
    __check_uuid(ict_net, uid)
    if uid is not None:
        if str(from_app) == str(uid):
            raise UserWarning("from_app and uid must not be equal")
        if str(to_app) == str(uid):
            raise UserWarning("to_app and uid must not be equal")  
        
def __create_connection_check_nouuid(from_app, to_app, peers):    
    __check_elts_and_get_index(from_app, 'from_app', 'app')         
    __check_elts_and_get_index(to_app, 'to_app', 'app', allow_list=False)
    if peers is not None:
        if not isinstance(peers[0], tuple) or not isinstance(peers[1], tuple):
            raise UserWarning("peers elements must be tuples (str, int)")
        if not (peers[0][0] == 'app' and peers[1][0] == 'app'):
            raise UserWarning("peers elements must be app-type")
        if (peers[0] == peers[1]):
            raise UserWarning("peers elements must not be the same")    

def __create_connection_check(ict_net, use_uuid, uid, from_app, to_app, peers):
    
    if peers is not None and (not isinstance(peers, tuple) or len(peers) != 2):
        raise UserWarning("peers must be a 2-tuple")
    if peers is not None and peers[0] == peers[1]:
        raise UserWarning("peers must not be equal")
    if use_uuid:
        __create_connection_check_uuid(ict_net, uid, from_app, to_app, peers)        
    else:
        __create_connection_check_nouuid(from_app, to_app, peers)    
        
      
def create_ict_connection(ict_net, name=None, index=None, in_service=True, use_uuid=False, uid=None,
                          from_app=None, to_app=None, protocol=None, info_items=None, **kwargs):       
     
    """
    Adds one connection in table ict_net["conn"].

    Connections represent end-to-end ICT connections between apps. Information items are transmitted over connections using 
    protocols, and may be physically routed through multiple links and nodes.  

    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which the connection is created      
        
        **from_app** ((string,int) or UUID4, default None) - connection start element, in pandaict element notation if use_uuid == False, \
            else as UUID. Element type must be app.     
        
        **to_app** ((string,int) or UUID4, default None) - connection end element, in pandaict element notation if use_uuid == False, \
            else as UUID. Element type must be app.  
        
    :OPTIONAL:
        **name** (string, default None) - The name for this connection.
        
        **index** (int, default None) - Force a specified list index if it is available. If None, the \
            index one higher than the highest already existing index is selected.

        **in_service** (boolean, default True) - True for in service or False for out of service.

        **use_uuid** (boolean, default False) - True if uuids shall be used; if False, pandaict element notation is used. 
        
        **uid** (UUID4 or string, default None) - user-selected uuid for this connection (must not be used in this network yet).            
            
        **protocol** (string, default None) - Protocol to be used for this connection. A standard protocol type may be used. \
            Note: a connection uses exactly one protocol. End-to-end communication using multiple protocols need multiple connections \
            as well as introduction of converter type apps. 
            
        **info_items** (list of aenum, default None) - Information items transmitted by the connection. Use INFO_ITEM type aenum. 
        
        **peers** (2-tuple of (string,int) or UUID4, default None) - element identifiers of non-converter type apps that are communication endpoints. \
            The pair refers to the app that originally produces information items, and the one which finally receives them. \
            If these communicate using different protocols, there are multiple connections and at least one converter-type app in between, \
            but the **peers** field is the same for all involved connections.    
        
        **producer** (list of <0 or 1>) - Indicates producers of information items. If **producer[n]** is 0, this means the info_items[n] is \
            produced by peers[0]. If **producer[n]** is 1, this means the info_items[n] is \
            produced by peers[1]. 
        
        **prod_freq_ms** (list of float) - Average frequency of information item generation. Each list item refers to the same index in **info_items**. \
            The value -1 means that the info item generation is event-based and not recurrent, such that no meaningful frequency can be given.  
            
    :OUTPUT:
        **elt** ((string,int) or UUID4) - The unique ID of the created element. If use_uuid==False, pandaict element notation is used, \
            otherwise a uuid is returned (either the user selected uid or a newly generated one).

    :EXAMPLE:
        create_ict_connection(net, from_elt = ("app", 1), to_elt = ("app", 3), protocol="HTTP")
    """
    
    peers = kwargs.get('peers', None)
    producer = kwargs.get('producer', None)
    prod_freq_ms = kwargs.get('prod_freq_ms', None)
    __create_net_index_check(ict_net, index, "conn")
    __create_connection_check(ict_net, use_uuid, uid, from_app, to_app, peers)                   
    __create_std_type_check(ict_net, protocol, (str), 'protocol')    
    __check_list_items(info_items, allowed_types=(InfoItem))
    il = len(info_items) if info_items is not None else None    
    __check_list_items(producer, allowed_length=il, allowed_types=(int), allowed_values=(0,1))
    __check_list_items(prod_freq_ms, allowed_length=il, allowed_types=(int, float))

    if index is None:
        index = __get_free_id(ict_net["conn"])        
    dtypes = ict_net.conn.dtypes
    ruuid  = __create_ruuid(uid, use_uuid)
    
    if (use_uuid):
        if peers is not None:
            pdev1 = get_elts_any(ict_net, peers[0], ["app"])                      
            pdev2 = get_elts_any(ict_net, peers[1], ["app"])
            peers = (pdev1[1], pdev2[1])
        else:
            peers = None        
        from_app = get_elts_any(ict_net, from_app, ["app"])         
        from_app = from_app[1]
        to_app   = get_elts_any(ict_net, to_app, ["app"])                
        to_app   = to_app[1]
    else:
        from_app = from_app[1] 
        to_app   = to_app[1]
        
    if from_app==to_app: 
        raise UserWarning("from_app and to_app must not be equal") 
            
    ict_net.conn.loc[index, ["name", "in_service", "from", "to", "protocol", "uuid" ]] = [name, in_service, from_app, to_app, protocol, ruuid]
    ict_net.conn.at[index,'info_items'] = info_items
    ict_net.conn.at[index,'peers'] = peers
    ict_net.conn.at[index,'producer'] = producer
    ict_net.conn.at[index,'prod_freq_ms'] = [float(p) for p in prod_freq_ms] if prod_freq_ms is not None else None
    
    __preserve_dtypes(ict_net.conn, dtypes)

    return ruuid if use_uuid else ('conn', int(index))

