'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 8.02.2024

@author: jringelstein
'''

list2str_delim = ";"

def list2str_set_delim(d):
    global list2str_delim
    list2str_delim = d

def list2str(l):
    global list2str_delim
    if not isinstance(l, list):
        return ""
    s = list2str_delim.join([str(ele) for ele in l])
    return s 

def str2list(s):
    global list2str_delim
    if not isinstance(s, str):
        return []
    l = s.split(list2str_delim)
    return l