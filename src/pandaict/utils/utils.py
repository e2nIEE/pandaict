'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.02.2024

@author: jringelstein
'''

import numpy as np 
import uuid

# Convert uuid to (elt_type, index) of element in ict_net
# Returns None if uuid not found anywhere in ict_net
def uuid2elt(ict_net, uid):    
    """
    Converts from UUID to pandaict element identifier.

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **uid** (UUID4) - UUID of an element that exists in ict_net     
                            
    :OUTPUT:
        **elt** (str,int) - ID of the element in pandaict element notation. Returns None if element not found in ict_net. 

    :EXAMPLE:
        uuid2elt(ict_net, uuid.UUID("0a004f60-1df4-449c-94b5-08809ad686d1"))
    """
    
    idx = None
    elt_types = ["node","link","device","app","conn"]    
    for et in elt_types:
        try:
            idx = np.where(ict_net[et]['uuid']==uid)[0][0]
            return (et, idx)
        except:
            pass            
    return None
    
# Convert (elt_type, index) of element in ict_net to uuid
# Returns None if uuid not available
def elt2uuid(ict_net, elt):
    """
    Converts from pandaict element identifier to UUID.

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **elt** (str, int) -pandaict identifier of an element that exists in ict_net     
                            
    :OUTPUT:
        **uid** (UUID4) - UUID of the element. Returns None if element not found in ict_net or element has no UUID. 

    :EXAMPLE:
        elt2uuid(ict_net, ('device',2))
    """    
    uid = None
    try:
        uid = get_elt(ict_net,elt)['uuid']
        return uid
    except:
        return None
    
    
def check_all_uuid(ids, allow_list=True):
    """
    Check if parameter is uuid4 or - in case it is a list - all elements are uuid4.
    Raises UserWarning if this is not the case.

    :INPUT:
        **ids** (any) - Parameter to be checked
        **allow_list** (boolean) - If True, lists are allowed and checked element-wise. If False, lists are considered non-uuid.              
                            
    :OUTPUT:
        None 
    
    """ 
    if ids is not None:
        if allow_list and isinstance(ids, list):
            for i in ids:
                if not isinstance(i, uuid.UUID):
                    raise UserWarning("list must only contain uuid4")
        elif not isinstance(ids, uuid.UUID):
            raise UserWarning("element must be uuid4")                    
    else:
        raise UserWarning("Element is None, must be uuid4")
def get_elt(ict_net, elt):
    """
    Fetch element by pandaict element identifier.

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **elt** (str, int) -pandaict identifier of an element that exists in ict_net     
                            
    :OUTPUT:
        **elt** (dict) - The pandaict element. 

    :EXAMPLE:
        get_elt(ict_net, ('device',2))
    """ 
    try:
        retval = ict_net[elt[0]].loc[elt[1]]
        return retval
    except:
        return None

def get_elt_by_uuid(ict_net, uid):
    """
    Fetch element by UUID.

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **elt** (dict) -pandaict identifier of an element that exists in ict_net     
                            
    :OUTPUT:
        **elt** (dict) - The pandaict element. 

    :EXAMPLE:
        get_elt(ict_net, uuid.UUID("0a004f60-1df4-449c-94b5-08809ad686d1"))
    """
    return get_elt(ict_net, uuid2elt(ict_net, uid))

def get_elts_any(ict_net, elt_ids, expected=None):           
    """
    Fetch single or multiple elements by any identifier.

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **elt_ids** (tuple, uuid or list) - pandaict identifier(s) of an element that exists in ict_net
        
    :OPTIONAL:
        **expected** (list of string, default None) - list of element types expected in the output. None means any types allowed. \
            UserWarning raised if a non-expected element type is found.
                            
    :OUTPUT:
        **elt** (dict or list of dict) - The pandaict element(s). 

    :EXAMPLES:
        get_elt(ict_net, uuid.UUID("0a004f60-1df4-449c-94b5-08809ad686d1"))
        get_elt(ict_net, ['device', 0], ['node, 3], expected=['device', 'node'])
    """
    if isinstance(elt_ids, list):
        _elt_ids = elt_ids
    else:
        _elt_ids = [elt_ids]
    
    elts = []
    for eid in _elt_ids:
        if isinstance(eid, uuid.UUID):
            elt = uuid2elt(ict_net, eid)
            if elt is None or None in elt:                
                raise UserWarning("at least one uuid elt not found by uuid")    
            if expected is not None and elt[0] not in expected:
                raise UserWarning("uuid elt type is "+str(elt)+" but must be one of "+str(expected))
        else:
            if expected is not None and eid[0] not in expected:
                raise UserWarning("elt type is "+str(eid)+" but must be one of "+str(expected))
            elt = get_elt(ict_net, eid)
        elts += [elt]         
                 
    return elts if isinstance(elt_ids, list) else elts[0]    

def get_apps_on_device(ict_net, device):
    """
    Fetch list of apps running on a pandaict device.

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **device** (str, int) - pandaict notation element identifier of a device that exists in ict_net     
                            
    :OUTPUT:    
        **applist** (list) - List of indexes of the ict_net.app table that reference apps running on the \
            device. Returns empty list if no apps found.              
              
    :EXAMPLE:
        get_apps_on_device(ict_net, ('device',2))
    """
    applist = []
    for i, a in ict_net.app.iterrows():    
        if a.device==device[1]:
            applist += [i]
    return applist

def get_links_at(ict_net, elt):
    """
    Fetch list of links that are connected to a pandaict element

    :INPUT:    
        **ict_net** (pandaictNet) - A pandaict network     

        **elt** (str, int) - pandaict notation element identifier of a node or device that exists in ict_net     
                            
    :OUTPUT:    
        **linklist** (list) - List of indexes of the ict_net.link table that that reference links which \
            have the element as one of their endpoints. Returns empty list if element is not node or device \
            or no links connected to element.

    :EXAMPLE:
        get_links_at(ict_net, ('device',2))
    """
    linklist = []
    if not(elt[0]=="node" or elt[0]=="device"):
        return []  
    
    for i, l in ict_net.link.iterrows():    
        if (isinstance(l['to'], list)):
            if elt==l['from'] or elt in l['to']:
                linklist += [i]
        else:
            if elt==l['from'] or elt==l['to']:
                linklist += [i]
    return linklist

def get_links_between(ict_net, elt1, elt2):    
    """
    Fetch list of links that are connecting two pandaict elements

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **elt1** (str, int) - pandaict notation element identifier of first element. Must be node or device.
        
        **elt2** (str, int) - pandaict notation element identifier of second element. Must be node or device.
                            
    :OUTPUT:
        **linklist** (list) - List of indexes of the ict_net.link table that reference links which \
            connect the two elements (either way). 

    :EXAMPLE:
        get_links_between(ict_net, ('device',2), ('node',1))
    """
    if not((elt1[0]=="device" or elt1[0]=="node") and (elt2[0]=="device" or elt2[0]=="node")):
        return []
    linklist = []
    for i, l in ict_net.link.iterrows():
        lfrom = l['from']
        lto   = l['to'] if isinstance(l['to'],list) else [l['to']]
        for eltto in lto:
            if {lfrom, eltto}=={elt1, elt2}:
                linklist += [i]
                break        
        
    return linklist

def is_bidirectional(ict_net, link_elt):
    """
    Check if a link is bidirectional

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **link_elt** (str, int) - The link's pandaict notation element identifier.                 
                            
    :OUTPUT:
        **bidirectional** (boolean) - True if link is bidirectional, False if unidirectional. 

    :EXAMPLE:
        is_bidirectional(ict_net, ('link',2))
    """
    if (not isinstance(link_elt, tuple) or link_elt[0] != "link"):
        return None
    bw = get_bandwidth_Mbps(ict_net, link_elt)
    return False if (isinstance(bw, float) or len(bw)<2 or bw[1]==0) else True  
   
def get_supported_protocols(ict_net, link_elt):       
    """
    Get protocols supported by a link

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **link_elt** (str, int) - The link's pandaict notation element identifier.                 
                            
    :OUTPUT:
        **protocols** (list) - List of supported protocol types 

    :EXAMPLE:
        get_supported_protocols(ict_net, ('link',2))
    """
    
    return ict_net.std_types['link'][ict_net.link.iloc[link_elt[1]]['type']]['protocols']  

def get_bandwidth_Mbps(ict_net, link_elt):     
    """
    Get bandwidth of a link

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **link_elt** (str, int) - The link's pandaict notation element identifier.                 
                            
    :OUTPUT:
        **bandwidth** (tuple) - Link bandwith in downstream/upstream direction 

    :EXAMPLE:
        get_bandwidth_Mbps(ict_net, ('link',2))
    """  
    
    return ict_net.std_types['link'][ict_net.link.iloc[link_elt[1]]['type']]['bandwidth_Mbps']  

