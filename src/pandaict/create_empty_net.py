'''
Created on 30.01.2024
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

from pandaict.auxiliary import pandaICTNet
from pandaict.std_types import add_basic_std_types
from numpy import dtype, zeros
import pandas as pd
from pandaict.pilogger import pilogger

def __get_node_structure():
    return [
        ("name", dtype(object)), 
        ("type", dtype(object)), 
        ("in_service", "bool"), 
        ("uuid", dtype(object)), 
        ("geodata", dtype(object)), 
        ("link_types", dtype(object)), 
        ("ber", "f8"), 
        ("mtbf_h", "f8"), 
        ("mttr_h", "f8")]


def __get_link_structure():
    return [
        ("name", dtype(object)), 
        ("type", dtype(object)), 
        ("in_service", "bool"), 
        ("uuid", dtype(object)), 
        ("from", dtype(object)), 
        ("to", dtype(object)), 
        ("length_km", "f8")]


def __get_device_structure():
    return [
        ("name", dtype(object)), 
        ("type", dtype(object)), 
        ("in_service", "bool"), 
        ("uuid", dtype(object)), 
        ("mtbf_h", "f8"), 
        ("mttr_h", "f8")]


def __get_app_structure():
    return [
        ("name", dtype(object)), 
        ("type", dtype(object)), 
        ("in_service", "bool"), 
        ("uuid", dtype(object)), 
        ("device", "u4"), 
        ("conversions", dtype(object))]


def __get_conn_structure():
    return [
        ("name", dtype(object)), 
        ("in_service", "bool"), 
        ("uuid", dtype(object)), 
        ("from", "u4"), 
        ("to", "u4"), 
        ("protocol", dtype(object)),
        ("info_items", dtype(object)), 
        ("peers", dtype(object)), 
        ("producer", dtype(object)), 
        ("prod_freq_ms", dtype(object))]

def create_empty_network(name="", add_stdtypes=True):
    """
    This function initializes the pandaict network datastructure.

    :OPTIONAL:        
        **name** (string, default "") - name for the network    

        **add_stdtypes** (boolean, default True) - Includes standard types to net

    :OUTPUT:
        **net** (pandaICTNet) - pandaict network with empty tables

    :EXAMPLE:
        ict_net = create_empty_network()

    """    
    ict_net = pandaICTNet({
        "name": name,       
        "node": __get_node_structure(),
        "link": __get_link_structure(),        
        "device": __get_device_structure(),  
        "app": __get_app_structure(),       
        "conn": __get_conn_structure(),
        "connectors": [], 
        "iptables": [],
        })

    if add_stdtypes:
        add_basic_std_types(ict_net)
    else:
        ict_net.std_types = {"link": {}, "protocol": {}}

    for s in ict_net:
        if isinstance(ict_net[s], list):
            ict_net[s] = pd.DataFrame(zeros(0, dtype=ict_net[s]), index=[])
    return ict_net
