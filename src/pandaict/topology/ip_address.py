'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.08.2024

@author: jringelstein
'''

import pandas as pd
import networkx as nx
import uuid
import re
from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __get_end_nxnodes_for_conn, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.utils.enums import RoutingType, SortType
from psutil._common import addr

class IP_address: 
            
    def __init__(self, ip_string):
        ip = ""
        netmask= None        
        self.from_string(ip_string)    
   
    def __repr__(self):
        if self.netmask is not None:
            return self.ip+" / "+self.netmask
        else:
            return self.ip
    
    def from_string(self, ip_string):
        if not(self.validate_ip(ip_string)):
            print("Invalid IP string: "+ip_string)
        if ':' in ip_string: 
            # assume IPv6
            print("IPv6 not supported yet")
        if '/' in ip_string: 
            (addr, prefix) = ip_string.split('/')
            self.ip = addr
            m = int(~((1 << (32-int(prefix))) - 1))
            self.netmask = str((m >> 24 & 255, m >> 16 & 255, m >> 8 & 255, m & 255)).replace('(','').replace(', ','.').replace(')','')
        else:
            self.ip = ip_string
            self.netmask = None
        
        
    def validate_ip(self, ip_string):
        try:
            if '.' in ip_string:
                pattern = "^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$"
                if re.match(pattern, ip_string) is None: 
                    return False                
                if '/' in ip_string: 
                    (addr, mask) = ip_string.split('/')
                    if int(mask)<0 or int(mask)>32: 
                        return False
                else:
                    addr = ip_string
                for b in addr.split('.'):
                    if int(b)>255 or int(b)<0: 
                        return False
        except:
            return False 
        
        return True    
    
    def is_IPV4(self):
        if ":" in self.ip:
            return False 
        else:
            return True
    
    def _ipv4_to_int(self, ip_string):
        (i4, i3, i2, i1) = ip_string.split(".")
        return int(i4) << 24 | int(i3) << 16 | int(i2) << 8 | int(i1)
    
    def _int_to_ipv4(self, i):
        return str((i >> 24 & 255, i >> 16 & 255, i >> 8 & 255, i & 255)).replace('(','').replace(', ','.').replace(')','')
    
    def is_IPV6(self):
        if ":" in self.ip:
            return True 
        else:
            return False        
    
    def split_cidr(self, cidr_ip):    
        if "." in cidr_ip: # IPv4
            ip, prefix = cidr_ip.split("/")        
            if prefix is not None:            
                if prefix <= 32:                    
                    mask = self._int_to_ipv4(int(~((1 << (32-prefix)) - 1)))
            return ip, mask
        
    def inc(self, own_network_only = False):
        # increase without respecting netmask
        if self.is_IPV4:            
            ip_int = self._ipv4_to_int(self.ip)            
            
            if own_network_only and self.netmask is not None:                
                mask_int = self._ipv4_to_int(self.netmask)
                host_ip = (ip_int & ~mask_int) + 1
                if (host_ip & 255) == 0:
                    host_ip += 1
                if (host_ip & 255) == 255:
                    host_ip += 2
                if host_ip > (~mask_int) & ((1 << 32) - 1):
                    return False
                else:
                    ip_int = (ip_int & mask_int) + host_ip                                        
            else: 
                ip_int += 1            
                if (ip_int & 255) == 0:
                    ip_int += 1
                if (ip_int & 255) == 255:
                    ip_int += 2
            self.ip = self._int_to_ipv4(ip_int)
            return True
        
    def last_hostIP_in_network(self):
        if self.is_IPV4:
            if self.netmask is None:
                return IP_address("255.255.255.254")
            else: 
                ip_int = self._ipv4_to_int(self.ip) 
                mask_int = self._ipv4_to_int(self.netmask)          
                n = bin(mask_int).count('1')
                lip = (ip_int & mask_int) + (1 << (32-n)) - 1
                if lip & 255 == 255: 
                    lip -= 1
                last_ip = IP_address(self._int_to_ipv4(lip))
                last_ip.netmask = self.netmask
                return last_ip
    
    def greater_than(self, ip_addr):
        ours_int = self._ipv4_to_int(self.ip)
        theirs_int = self._ipv4_to_int(ip_addr.ip)
        return ours_int > theirs_int