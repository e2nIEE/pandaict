'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.02.2024

@author: jringelstein
'''

import numpy as np 

str_delim = ";"

def set_str_delim(d):
    global str_delim
    str_delim = d

def list2str(l):
    global str_delim
    if not isinstance(l, list):
        return ""
    s = str_delim.join([str(ele) for ele in l])
    return s 

def str2list(s):
    global str_delim
    if not isinstance(s, str):
        return []
    l = s.split(str_delim)
    return l

def tuple2str(t):
    global str_delim
    if not isinstance(t, tuple):
        return ""
    s = str_delim.join([str(ele) for ele in t])
    return s 

def str2tuple(s):
    global str_delim
    if not isinstance(s, str):
        return []
    l = tuple(s.split(str_delim))
    return l

# Convert uuid to (elt_type, index) of element in ict_net
# Returns None if uuid not found anywhere in ict_net
def uuid2elt(ict_net, uid):    
    try:
        idx = np.where(ict_net.node['uuid']==uid)[0][0]
        #idx = ict_net.node.loc[ict_net.node['uuid']==uid].index(0)
    except:
        idx = None
    return idx