"""
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.08.2024

@author: jringelstein
"""

import re
from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __get_end_nxnodes_for_conn, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.utils.enums import RoutingType, SortType
from pandaict.pilogger import pilogger

class IP_address: 
    """
        Class for IP address handling (currently only IPv4)
    """        
    def __init__(self, ip_string, netmask_string=None):
        """
        Constructs an IP address object.
        
        :INPUT:
            **ip_string** (string) - IP address in string representation, e.g. "10.2.2.1". May use CIDR notation, e.g. "10.2.2.1/22". \
                If CIDR notation is used and netmask_string is omitted, the netmasks will be derated using the CIDR notation.
        
        :OPTIONAL:
            **netmask_string** (string, default None) - Netmask in string representation, e.g. "255.255.255.0". \
                Note: if the IP is given using CIDR notation, netmask_string will be ignored. 
            
        """ 
        self.ip = ""
        self.netmask= None        
        self.from_string(ip_string)    
        if netmask_string is not None and self.netmask is None: 
            self.netmask = netmask_string
   
    def __repr__(self):
        if self.netmask is not None:
            return self.ip+" / "+self.netmask
        else:
            return self.ip
    
    def from_string(self, ip_string):
        """
        Converts string into IP and netmask and stores result in current IP_address object
        
        :INPUT:
            **ip_string** (string) - IP address in string representation, e.g. "10.2.2.1". May use CIDR notation, e.g. "10.2.2.1/22". \
                If CIDR notation is used and netmask_string is omitted, the netmaks will be derated using the CIDR notation.
                    
        """ 
        if not(self.__validate_ip(ip_string)):
            pilogger.error("Invalid IP string: "+ip_string)
        if ':' in ip_string: 
            # assume IPv6
            pilogger.error("IPv6 not supported yet")
        if '/' in ip_string: 
            (addr, prefix) = ip_string.split('/')
            self.ip = addr
            m = int(~((1 << (32-int(prefix))) - 1))
            self.netmask = self.__int_to_ipv4(m)                               
        else:
            self.ip = ip_string
            self.netmask = None
        
        
    def __validate_ip(self, ip_string):
        try:
            if '.' in ip_string:
                pattern = r"^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$"
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
        except (AttributeError, ValueError, IndexError, TypeError):
            return False 
        
        return True    
    
    def is_IPV4(self):
        """
        Checks if object is an IPv4 address
        
        :OUTPUT:
            **ipv4** (boolean) - True if IPv4 detected, False otherwise
                        
        """ 
        if ":" in self.ip:
            return False 
        else:
            return True
    
    def __ipv4_to_int(self, ip_string):
        (i4, i3, i2, i1) = ip_string.split(".")
        return int(i4) << 24 | int(i3) << 16 | int(i2) << 8 | int(i1)
    
    def __int_to_ipv4(self, i):
        return str((i >> 24 & 255, i >> 16 & 255, i >> 8 & 255, i & 255)).replace('(','').replace(', ','.').replace(')','')    
        
    def inc(self, own_network_only = False):
        """
        Increases IP, with or without respecting netmask.
        IP is usually increased by one, but the host IP ending values 0 and 255 are avoided (reserved for network and broadcast) 
        
        :OPTIONAL:
            **own_network_only** (boolean, default False) - If True, the IP is not increased if it would leave the own network address space. If False, \
                the IP is increased anyhow. 
            
        :OUTPUT:
            **success** (boolean) - True if IP was successfully increased, False if increasing was not possible
                        
        """ 
        if not self.is_IPV4():
            pilogger.error("Only IPV4 supported")
            return False
        
        ip_int = self.__ipv4_to_int(self.ip)            
        
        if own_network_only and self.netmask is not None:                
            mask_int = self.__ipv4_to_int(self.netmask)
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
        self.ip = self.__int_to_ipv4(ip_int)
        return True
        
    def last_hostIP_in_network(self):
        """
        Calculates highest possible host IP in this IP's network 
        
        :OUTPUT:
            **last_ip** (IP_address) - IP_address object representing the highest host IP in the network 
                                    
        """ 
        if not self.is_IPV4():
            pilogger.error("Only IPV4 supported")
            return False
        
        if self.netmask is None:
            return IP_address("255.255.255.254")
        else: 
            ip_int = self.__ipv4_to_int(self.ip) 
            mask_int = self.__ipv4_to_int(self.netmask)          
            n = bin(mask_int).count('1')
            lip = (ip_int & mask_int) + (1 << (32-n)) - 1
            if lip & 255 == 255: 
                lip -= 1
            last_ip = IP_address(self.__int_to_ipv4(lip))
            last_ip.netmask = self.netmask
            return last_ip

    def greater_than(self, other):
        """
        Determines if current IP is greater than another one 
        
        :INPUT:
            **other** (IP_address) - IP address object to compare to
            
        :OUTPUT:
            **is_greater** (boolean) - True if current IP is greater than ip_addr, False otherwise  
                                    
        """
        ours_int = self.__ipv4_to_int(self.ip)
        theirs_int = self.__ipv4_to_int(other.ip)
        return ours_int > theirs_int
    
    def is_same_network(self, other):
        """
        Determines if other IP is in the same network as current IP 
        
        :INPUT:
            **other** (IP_address) - IP address object to check
            
        :OUTPUT:
            **same_network** (boolean) - True if other IP is in the same network as current IP, False otherwise  
                                    
        """
        nwaddr1 = self.__ipv4_to_int(self.ip) & self.__ipv4_to_int(self.netmask) 
        nwaddr2 = self.__ipv4_to_int(other.ip) & self.__ipv4_to_int(other.netmask) 
        return nwaddr1==nwaddr2 
            