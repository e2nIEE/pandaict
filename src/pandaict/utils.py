'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.02.2024

@author: jringelstein
'''

import numpy as np 

list_delim = ";"
tuple_delim = "#"

def set_str_delim(d):
    global list_delim
    list_delim = d

def list2str(l):
    global list_delim
    if not isinstance(l, list):
        return ""
    s = list_delim.join([str(ele) for ele in l])
    return s 

def str2list(s):
    global list_delim
    if not isinstance(s, str):
        return []
    l = s.split(list_delim)
    return l

def tuple2str(t):
    global tuple_delim
    if not isinstance(t, tuple):
        return ""
    s = tuple_delim.join([str(ele) for ele in t])
    return s 

def str2tuple(s):
    global tuple_delim
    if not isinstance(s, str):
        return []
    l = tuple(s.split(tuple_delim))
    return l

# Convert uuid to (elt_type, index) of element in ict_net
# Returns None if uuid not found anywhere in ict_net
def uuid2elt(ict_net, uid):    
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
        idx = np.where(ict_net.conn['uuid']==uid)[0][0]
        return ('conn', idx)
    except:
        pass
    
# Convert (elt_type, index) of element in ict_net to uuid
# Returns None if uuid not available
def elt2uuid(ict_net, elt):    
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

def get_elt_by_uuid(ict_net, uid):
    return get_elt(uuid2elt(uid))
    
    
    