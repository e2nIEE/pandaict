'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.08.2024

@author: jringelstein
'''

import pandas as pd
import networkx as nx
import uuid
from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __get_end_nxnodes_for_conn, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.topology.ip_address import IP_address
from pandaict.utils.enums import RoutingType, SortType, NodeType
from pilogger import pilogger


def init_extend_network(ict_net):
    '''
        Prepares extending existing pandaICT network by IP-specific information 
    '''
    ict_net['iptables'] = {}
    ict_net.device.insert(4, "ip_addr", [None]*len(ict_net.device))
    ict_net.device.insert(4, "netmask", [None]*len(ict_net.device))
    ict_net.node.insert(4, "ip_addr", [None]*len(ict_net.node))
    ict_net.node.insert(4, "netmask", [None]*len(ict_net.node))
    
    # Example: 
    # ict_net.iptable = {1: [{"dest": "192.168.0.1/24", "gateway": "192.168.0.1/24"}, {"dest": "default", "gateway": "192.168.0.1/24"}]}

def __check_elt_to_assign(ict_net, e):
    if not isinstance(e, tuple): 
        pilogger.warning("Invalid value found in eltlist - skipping")
        return False
    if not(e[0]=='device' or e[0]=='node'):
        pilogger.warning("Element other than devices and nodes found in eltlist - skipping")
        return False 
    if e[0]=='node':
        n = get_elts_any(ict_net, e) 
        if n.type is not NodeType.ROUTER:
            pilogger.warning("Non-router node element found in eltlist - skipping")
            return False
    return True 

def assign_ipaddr_to_elts(ict_net, eltlist, start_ip=None, end_ip=None, netmask=None, ip_range=None):
    '''
        Subsequently assigns IP addresses to nodes and devices in eltlist using given address range 
        Elements need to be router-type nodes or devices. Other element types are ignored.
        The IP address range to be used can be given explicitly (start end end IP address) or using CIDR notation.
        
        :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **eltlist** (list of tuple) - list of elements in pandaICT elements notation. Elements other than devices or nodes are ignored.  
        
        **start_ip** (string) - IP to assign to the first element in eltlist. May use CIDR notation, where mask is used as netmask \
                                overriding the netmask parameter. 
                

        :OPTIONAL:
        
        **end_ip** (string) - Last IP in usable address range. May use CIDR notation but mask is ignored. Only respected if start_ip is used. \
                        If start_ip contains a mask (cidr notation), end_ip is ignored but the ip range comprises start_ip to the highest host ip \ 
                        in the same IP network
        
        **ip_range** (string) - Alternative option for IP address range. IP in CIDR notation. The address range comprises the whole IP subnet \
                                indicated by this. E.g. ip_range=10.0.0.1/24 translates to start_ip=10.0.0.1, end_ip=10.0.0.254
            
        **netmask** (string) - Netmask, which is also assigned to elements. If start_ip is given in CIDR notation \  
                            or ip_range is used, this parameter will be ignored but instead the mask from start_ip/ip_range is used. 
                            
    :OUTPUT:
        **(complete, next_free_ip)** (boolean, string) - If complete is True, all elements in the list (except invalid ones) were assigned an IP. If False, \
                            the IP address range was insufficient for that. next_free_ip is the next IP within the address range that was not assigned to an element. \
                            It is None if the address range was fully used.    

    :EXAMPLE:
        assign_ipaddr_to_elts(ict_net, [('device',1),('node',4),('node',5)], start_ip="10.0.0.1", end_ip="10.0.0.1", netmask="255.255.255.0")
        # Alternative equivalent to this:
        assign_ipaddr_to_elts(ict_net, [('device',1),('node',4),('node',5)], ip_range="10.0.0.1/24")
         
    '''
    if start_ip is not None:         
        cur_ip  = IP_address(start_ip)
        last_ip = None        
        if cur_ip.netmask is None and netmask is not None:
            cur_ip.netmask = netmask                
        if end_ip is not None: 
            last_ip  = IP_address(end_ip)
        elif cur_ip.netmask is None:
            pilogger.error("since end_ip is not used, start_ip must contain mask, using cidr notation") 
            return            
    elif ip_range is not None: 
        cur_ip = IP_address(ip_range)
        last_ip = None  
        if cur_ip.netmask is None:
            pilogger.error("ip_range must contain mask, using cidr notation")
            return 

    for e in eltlist:
        if not __check_elt_to_assign(ict_net, e):             
            continue        
        ict_net[e[0]].at[e[1],'ip_addr'] = cur_ip.ip
        ict_net[e[0]].at[e[1],'netmask'] = cur_ip.netmask
        inc_success = cur_ip.inc(own_network_only = (last_ip is None))         
        if (not inc_success) or (last_ip is not None and cur_ip.greater_than(last_ip)):
            return (e==eltlist[-1], None)
                
    return (True, cur_ip.ip) 
        

def update_iptables(ict_net, luptable):
    '''
        Adds routing information from a luptable to involved nodes  
    '''
    pass
    
def get_iptable(ict_net, node_elt):
    '''
        Get routing table for node  
    '''
    pass

def set_static_iptable_entry(ict_net, node_elt, to_ip, network_mask, gateway, out_link):
    '''
        Set static routing table entry for a node  
    '''
    pass

def calc_iptables(ict_net, routing_type):
    '''
        Calculate iptables for all hosts and router-type nodes  
    '''