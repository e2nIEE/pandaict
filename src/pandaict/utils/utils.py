'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.02.2024

@author: jringelstein
'''

import numpy as np 

# Convert uuid to (elt_type, index) of element in ict_net
# Returns None if uuid not found anywhere in ict_net
def __uuid2elt(ict_net, uid):    
    idx = None
    try:
        idx = np.where(ict_net.node['uuid']==uid)[0][0]
        return ('node', idx)
    except:
        pass
    
    try:
        idx = np.where(ict_net.link['uuid']==uid)[0][0]
        return ('link', idx)
    except:
        pass
    
    try:
        idx = np.where(ict_net.device['uuid']==uid)[0][0]
        return ('device', idx)
    except:
        pass
    
    try:
        idx = np.where(ict_net.app['uuid']==uid)[0][0]
        return ('app', idx)
    except:
        pass
    
    try:
        idx = np.where(ict_net.conn['uuid']==uid)[0][0]
        return ('conn', idx)
    except:
        pass
    
    return None
    
# Convert (elt_type, index) of element in ict_net to uuid
# Returns None if uuid not available
def __elt2uuid(ict_net, elt):    
    uid = None
    try:
        uid = ict_net[elt[0]].loc[elt[1]]['uuid']
        return uid
    except:
        return None
    
def get_elt(ict_net, elt):
    try:
        retval = ict_net[elt[0]].loc[elt[1]]
        return retval
    except:
        return None

def __get_elt_by_uuid(ict_net, uid):
    return get_elt(__uuid2elt(uid))

def __get_apps_on_device(ict_net, device):
    applist = []
    for i, a in ict_net.app.iterrows():    
        if a.device==device[1]:
            applist += [i]
    return applist

def __get_links_at(ict_net, elt):
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

def __get_links_between(ict_net, elt1, elt2):    
    if not((elt1[0]=="device" or elt1[0]=="node") and (elt2[0]=="device" or elt2[0]=="node")):
        return []
    linklist = []
    for i, l in ict_net.link.iterrows():
        lfrom = l['from']
        if isinstance(l['to'], list):
            continue
        lto   = l['to'] # only takes first element if it's a list #ToDo does this make sense?              
        if (lfrom==elt1 and lto==elt2) or (lfrom==elt2 and lto==elt1):
            linklist += [i]
    return linklist
            
    