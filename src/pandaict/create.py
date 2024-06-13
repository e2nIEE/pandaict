'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from pandaict.auxiliary import pandaICTNet
from pandaict.auxiliary import ADict, __get_free_id, __preserve_dtypes
from pandaict.create_empty_net import create_empty_network
from pandaict.utils.utils import uuid2elt, elt2uuid
from pandaict.utils.enums import InfoItem, NodeType, DeviceType, AppType
from pandaict.pilogger import pilogger
import uuid



def __create_uuid2elt(ict_net, elt_uuid, expected): 
       
    if isinstance(elt_uuid, list):
        elt = [uuid2elt(ict_net, uid) for uid in elt_uuid]
        if elt is None or None in elt:                
            raise UserWarning("at least one uuid elt not found by uuid")
        if not all((e[0] in expected) for e in elt):
            raise UserWarning("all uuid elt types must be one of "+str(expected))        
    else:
        elt = uuid2elt(ict_net, elt_uuid)
        if elt is None:                
            raise UserWarning("uuid elt not found by uuid")
        if not (elt[0] in expected):
            raise UserWarning("uuid elt type is "+str(elt[0])+" but must be one of "+str(expected))
             
    return elt    

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
    return

def __create_link_type_check(ict_net, link_type):
    
    if link_type is not None:
        if not isinstance(link_type, str):
                raise UserWarning("link_type must be str") 
        elif not link_type in ict_net.std_types['link'].keys():
            raise UserWarning("link_type "+str(link_type)+" not found in std_types")
    return

def __create_protocols_check(ict_net, protocols):
    
    if protocols is not None: 
        if isinstance(protocols, list):
            for pr in protocols: 
                if not pr in ict_net.std_types['protocol'].keys():
                    raise UserWarning("protocol "+str(pr)+" not found in std_types")
        elif not protocols in ict_net.std_types['protocol'].keys():
            raise UserWarning("protocol "+str(protocols)+" not found in std_types")
    return

def __check_uuid(ict_net, uid):
    if uid is not None:
        if not isinstance(uid, uuid.UUID) and not isinstance(uid, str):
            raise UserWarning("uid must be None, uuid4 or string")
        try:
            uelt = uuid2elt(ict_net, uuid.UUID(str(uid)))
        except:
            raise UserWarning("uid '" + str(uid) + "' can not be converted to UUID object")
        if uelt is not None:
            raise UserWarning("uid already in use for " + str(uuid2elt(ict_net, uuid.UUID(str(uid)))))

def __create_ict_node_check__(ict_net, node_type, index, uid, geodata, link_types):
    
    __create_net_index_check(ict_net, index, "node")
    if node_type is not None and not isinstance(node_type, NodeType):
        raise UserWarning("node_type must be NodeType")
    if geodata is not None:
        if isinstance(geodata, dict):
            if not "type" in geodata.keys() or not "coordinates" in geodata.keys():
                raise UserWarning("geodata must contain 'type' and 'coordinates' keys") 
        elif not isinstance(geodata, tuple) or not len(geodata)==2 or not isinstance(geodata[0], float) or not isinstance(geodata[0], float):         
            raise UserWarning("geodata must be (float, float) tuple or geojson")             
    if link_types is not None:
        if isinstance(link_types, list):
            for lt in link_types:
                if not lt in ict_net.std_types['link'].keys():
                    raise UserWarning("link_type " + str(lt) + " not found in std_types")        
        elif not link_types in ict_net.std_types['link'].keys():
            raise UserWarning("link_type " + str(link_types) + " not found in std_types")
    __check_uuid(ict_net, uid)
    return 

def create_ict_node(ict_net, name=None, node_type=None, index=None, in_service=True, use_uuid=False, uid=None, 
                     geodata=None, link_types=None, ber=0, mtbf_h=0, mttr_h=0):
    """
    Adds one node in table ict_net["node"].

    Nodes are network elements that can support connection of different physical links, and route data on ISO/OSI layers 1-3.

    INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which the node is created    

    OPTIONAL:
        **name** (string, default None) - the name for this node

        **node_type** (aenum, default None) - the node type. Use an NODE_TYPE aenum. 
        
        **index** (int, default None) - Force a specified list index if it is available. If None, the \
            index one higher than the highest already existing index is selected.

        **in_service** (boolean, default True) - True for in_service or False for out of service

        **use_uuid** (boolean, default False) - True if uuids shall be used; if false, pandaict element notation is used 
        
        **uid** (UUID4 or string, default None) - user-selected uuid for this node (must not be used in this network yet)
        
        **geodata** ((x,y)-tuple or GeoJSON Point, default None) - coordinates used for plotting
        
        **link_types** (aenum, default None) - link types supported by the node. Standard link types can be used. 
       
        **ber** (float, 0) - Bit error rate for this node, in p.u.

        **mtbf_h** (float, 0) - Mean time before failure for this node, in hours. Zero means not defined.
        
        **mttr_h** (float, 0) - Mean time to repair for this node, in hours. Zero means not defined.

    OUTPUT:
        **elt** ((str,int) or UUID4) - The unique ID of the created element. If use_uuid==False, the pandaict element notation is used (tuple of (str, int)), \
            otherwise a uuid is returned (either the user selected uid or a newly generated one)

    EXAMPLE:
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
    
    return ruuid if use_uuid else ('node', index)

def __create_ict_link_check(ict_net, from_elt, to_elt, uid, use_uuid):
    
    if use_uuid: 
        if from_elt is None or not isinstance(from_elt, uuid.UUID):
            raise UserWarning("from_elt must be uuid4")
        if to_elt is None or not (isinstance(to_elt, uuid.UUID) or isinstance(to_elt, list)):
            raise UserWarning("to_elt must be uuid4 or list of uuid4")
        if isinstance(to_elt, list):
            for i in range(0, len(to_elt)):
                if not isinstance(to_elt[i], uuid.UUID):
                    raise UserWarning("to_elt[" + str(i) + "] must be uuid4")        
        if from_elt == to_elt:
            raise UserWarning("from_elt and to_elt must not be equal")        
        __check_uuid(ict_net, uid)
        if uid is not None:
            if str(from_elt) == str(uid): 
                raise UserWarning("from_elt and uid must not be equal")
            if str(to_elt) == str(uid):         
                raise UserWarning("to_elt and uid must not be equal")        
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
    return 

def create_ict_link(ict_net, from_elt, to_elt, name=None, link_type=None, index=None, in_service=True, use_uuid=False, uid=None,
                    length_km=0 ):
    
    """
    Adds one link in table ict_net["link"].

    Links represent physical point-to-point ICT connections from device to node or in-between nodes. 

    INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which the link is created    

        **from_elt** ((string,int) or UUID4) - Link start element, in pandaict element notation if use_uuid == False, \
            else as UUID. Element type must be device or node.     
        
        **to_elt** ((string,int) or UUID4) - Link end element, in pandaict element notation if use_uuid == False, \
            else as UUID. Element type must be device or node. 
        
    OPTIONAL:
        **name** (string, default None) - the name for this link.

        **link_type** (string, default None) - the link type. Standard link type can be used.  
        
        **index** (int, default None) - Force a specified list index if it is available. If None, the \
            index one higher than the highest already existing index is selected.

        **in_service** (boolean, default True) - True for in_service or False for out of service.

        **use_uuid** (boolean, default False) - True if uuids shall be used; if false, pandaict element notation is used. 
        
        **uid** (UUID4 or string, default None) - user-selected uuid for this link (must not be used in this network yet).
        
        **length_km** (float, default 0) - Link line length for wired link type, or air distance for wireless link types.
            
    OUTPUT:
        **elt** ((string,int) or UUID4) - The unique ID of the created element. If use_uuid==False, pandaict element notation is used, \
            otherwise a uuid is returned (either the user selected uid or a newly generated one).

    EXAMPLE:
        create_ict_link(net, from_elt = ("node", 1), to_elt = ("device", 3), link_type="Binary")
    """
    
    __create_net_index_check(ict_net, index, "link")    
    __create_ict_link_check(ict_net, from_elt, to_elt, uid, use_uuid)                     
    __create_link_type_check(ict_net, link_type)
    
    if index is None:
        index = __get_free_id(ict_net["link"])
    dtypes = ict_net.link.dtypes        
    ruuid = __create_ruuid(uid, use_uuid)
    
    if (use_uuid):                 
        from_elt = __create_uuid2elt(ict_net, from_elt, expected=['device','node'])        
        to_elt = __create_uuid2elt(ict_net, to_elt, expected=['device','node'])                          
        
    if from_elt==to_elt: 
        raise UserWarning("from_elt and to_elt must not be equal") 
    if from_elt in to_elt:
        raise UserWarning("to_elt must not contain from_elt") 
            
    ict_net.link.loc[index, ["name", "type", "in_service", "length_km", "uuid"]] = [name, link_type, in_service, length_km, ruuid]
    ict_net.link.at[index,'from'] = from_elt
    ict_net.link.at[index,'to'] = to_elt

    __preserve_dtypes(ict_net.link, dtypes)

    return ruuid if use_uuid else ('link', index)

def __create_device_check(ict_net, device_type, uid):
    
    if device_type is not None and not isinstance(device_type, DeviceType):
        raise UserWarning("device_type must be DeviceType")
    __check_uuid(ict_net, uid)
    return

def create_ict_device(ict_net, name=None, device_type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      mtbf=0, mttr=0 ):
    
    """
    Adds one device in table ict_net["device"].

    Devices are physical communication endpoints. A device is connected to one or more node(s) by links, and is running one or more Apps.  
    Converters are a special type of device, running apps which convert between different protocols (ISO/OSI level >=4) 
    
    INPUT:
        **ict_net** (pandaictNet) - The pandaict network in which the node is created    

    OPTIONAL:
        **name** (string, default None) - the name for this node

        **node_type** (aenum, default None) - the node type. Use an NODE_TYPE aenum. 
        
        **index** (int, default None) - Force a specified list index if it is available. If None, the \
            index one higher than the highest already existing index is selected.

        **in_service** (boolean, default True) - True for in_service or False for out of service

        **use_uuid** (boolean, default False) - True if uuids shall be used; if false, pandaict element notation is used 
        
        **uid** (UUID4 or string, default None) - user-selected uuid for this node (must not be used in this network yet)
        
        **geodata** ((x,y)-tuple or GeoJSON Point, default None) - coordinates used for plotting
        
        **link_types** (aenum, default None) - link types supported by the node. Standard link types can be used. 
       
        **ber** (float, 0) - Bit error rate for this node, in p.u.

        **mtbf_h** (float, 0) - Mean time before failure for this node, in hours. Zero means not defined.
        
        **mttr_h** (float, 0) - Mean time to repair for this node, in hours. Zero means not defined.

    OUTPUT:
        **elt** ((str,int) or UUID4) - The unique ID of the created element. If use_uuid==False, the pandaict element notation is used (tuple of (str, int)), \
            otherwise a uuid is returned (either the user selected uid or a newly generated one)

    EXAMPLE:
        create_ict_node(net, name = "Node1")
    """
    
    __create_net_index_check(ict_net, index, "device")    
    __create_device_check(ict_net, device_type, uid)  

    if index is None:
        index = __get_free_id(ict_net["device"])
    dtypes = ict_net.device.dtypes        
    ruuid = __create_ruuid(uid, use_uuid)
        
    ict_net.device.loc[index, ["name", "type", "in_service", "mtbf", "mttr", "uuid" ]] = [name, device_type, in_service, mtbf, mttr, ruuid]

    __preserve_dtypes(ict_net.device, dtypes)

    return ruuid if use_uuid else ('device', index)
     
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
    return

def create_ict_app(ict_net, name=None, app_type=None, index=None, in_service=True, use_uuid=False, uid=None,                      
                      conversions=None, device=None ):
    
    __create_net_index_check(ict_net, index, "app")    
    __create_app_check(ict_net, name, app_type, uid, conversions, device)
                
    if index is None:
        index = __get_free_id(ict_net["app"])
    dtypes = ict_net.app.dtypes
    ruuid = __create_ruuid(uid, use_uuid)
    
    if (use_uuid):
        rdevice = uuid2elt(ict_net, device) 
        if rdevice is None:
            raise UserWarning("device not found by uuid") 
        if not rdevice[0]=='device': 
            raise UserWarning("device parameter is "+str(rdevice[0])+", must be device")
        rdevice = rdevice[1]
    else:
        if not device[0]=='device': 
            raise UserWarning("device parameter is "+str(device[0])+", must be device")  
        rdevice = device[1]
        
    ict_net.app.loc[index, ["name", "type", "in_service", "uuid", "device" ]] = [name, app_type, in_service, ruuid, rdevice]
    ict_net.app.at[index, "conversions"] = conversions

    __preserve_dtypes(ict_net.app, dtypes)

    return ruuid if use_uuid else ('app', index)

def create_ict_devapp(ict_net, name=None, device_type=None, app_type=None, in_service=True, use_uuid=False,            
                      conversions=None, mtbf=0, mttr=0 ):
    
    dev = create_ict_device(ict_net, name=name, device_type=device_type, in_service=in_service, use_uuid=use_uuid, mtbf=mtbf, mttr=mttr)    
    app = create_ict_app(ict_net, name=name, app_type=app_type, in_service=in_service, use_uuid=use_uuid, conversions=conversions, device=dev)
    return (dev, app)

def __create_connection_check(ict_net, use_uuid, uid, from_app, to_app, peers):
    
    if peers is not None and (not isinstance(peers, tuple) or not len(peers) == 2):
        raise UserWarning("peers must be a 2-tuple")
    if peers is not None and peers[0] == peers[1]:
        raise UserWarning("peers must not be equal")
    if use_uuid:
        if from_app is None or not isinstance(from_app, uuid.UUID):
            raise UserWarning("from_app must be uuid4")
        if to_app is None or not isinstance(to_app, uuid.UUID):
            raise UserWarning("to_app must be uuid4")
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
    else:
        if not isinstance(from_app, tuple):
            raise UserWarning("from_app must be (str, int) tuple")
        if not (from_app[0] == 'app'):
            raise UserWarning("from_app is " + str(from_app[0]) + ", must be app")
        if not isinstance(to_app, tuple):
            raise UserWarning("to_app must be (str, int) tuple")
        if not (to_app[0] == 'app'):
            raise UserWarning("to_app is " + str(to_app[0]) + ", must be app")
        if peers is not None:
            if not isinstance(peers[0], tuple) or not isinstance(peers[1], tuple):
                raise UserWarning("peers elements must be tuples (str, int)")
            if not (peers[0][0] == 'app' and peers[1][0] == 'app'):
                raise UserWarning("peers elements must be app-type")

def __create_connection_info_items_check(info_items, producer, prod_freq_ms):
    
    if info_items is not None:
        if not isinstance(info_items, list):
            raise UserWarning("info_items must be a list of InfoItem")
        for ii in info_items:
            if not isinstance(ii, InfoItem):
                raise UserWarning("info_items must be a list of InfoItem")
    
    if producer is not None:
        if not isinstance(producer, list):
            raise UserWarning("producer must be None or list")
        if len(producer) != len(info_items) or not all((p == "0" or p == "1") for p in producer):
            raise UserWarning("producer length must be the same as info_items, and all entries must be 0 or 1")
    if prod_freq_ms is not None:
        if not isinstance(prod_freq_ms, list):
            raise UserWarning("prod_freq_ms must be None or list")
        if len(prod_freq_ms) != len(info_items) or not all((isinstance(p, float) for p in prod_freq_ms)):
            raise UserWarning("prod_freq_ms length must be the same as info_items, and all entries must be float.")

def create_ict_connection(ict_net, name=None, index=None, in_service=True, use_uuid=False, uid=None,
                          from_app=None, to_app=None, protocol=None, info_items=None, **kwargs):       
     
    peers = kwargs.get('peers', None)
    producer = kwargs.get('producer', None)
    prod_freq_ms = kwargs.get('prod_freq_ms', None)
    __create_net_index_check(ict_net, index, "conn")
    __create_connection_check(ict_net, use_uuid, uid, from_app, to_app, peers)                   
    __create_protocols_check(ict_net, protocol)    
    __create_connection_info_items_check(info_items, producer, prod_freq_ms)

    if index is None:
        index = __get_free_id(ict_net["conn"])        
    dtypes = ict_net.conn.dtypes
    ruuid  = __create_ruuid(uid, use_uuid)
    
    if (use_uuid):
        if peers is not None:
            pdev1 = __create_uuid2elt(ict_net, peers[0], ["app"])                      
            pdev2 = __create_uuid2elt(ict_net, peers[1], ["app"])
            peers = (pdev1[1], pdev2[1])
        else:
            peers = None        
        from_app = __create_uuid2elt(ict_net, from_app, ["app"])         
        from_app = from_app[1]
        to_app   = __create_uuid2elt(ict_net, to_app, ["app"])                
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
    ict_net.conn.at[index,'prod_freq_ms'] = prod_freq_ms

    __preserve_dtypes(ict_net.conn, dtypes)

    return ruuid if use_uuid else ('conn', index)

