'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.08.2024

@author: jringelstein
'''

import pandas as pd
import networkx as nx
import uuid
from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links, get_links_at, flatten2d
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __get_end_nxnodes_for_conn, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.topology.ip_address import IP_address
from pandaict.utils.enums import RoutingType, SortType, NodeType
from pilogger import pilogger


def init_extend_network(ict_net):
    '''
        Prepares extending existing pandaICT network by IP-specific information 
    '''
    ict_net.iptables = pd.DataFrame(columns=["node_idx", "entry", "destination", "netmask", "gateway", "link_idx", "type", "metric"])
    ict_net.device.insert(4, "ip_addr", [None]*len(ict_net.device))
    ict_net.device.insert(4, "netmask", [None]*len(ict_net.device))
    ict_net.node.insert(4, "ip_addr", [None]*len(ict_net.node))
    ict_net.node.insert(4, "netmask", [None]*len(ict_net.node))
    
    # Example: 
    # ict_net.iptable = {1: [{"dest": "192.168.0.1/24", "gateway": "192.168.0.1/24"}, {"dest": "default", "gateway": "192.168.0.1/24"}]}

def __get_ipaddr_by_element(ict_net, e):
    if e[0]=='device':
        return ict_net.device.iloc[e[1]].ip_addr
    elif e[0]=='node':
        return ict_net.node.iloc[e[1]].ip_addr
    else:
        return None
    
def __get_netmask_by_element(ict_net, e):
    if e[0]=='device':
        return ict_net.device.iloc[e[1]].netmask
    elif e[0]=='node':
        return ict_net.node.iloc[e[1]].netmask
    else:
        return None
    
def __get_element_by_ipaddr(ict_net, ip):
    # try to find in devices
    dev_idx = ict_net.device[ict_net.device.ip_addr==ip].index 
    if not dev_idx.empty: 
        return ('device', dev_idx[0])
    # try to find in nodes (which can have multiple IPs)
    mask = ict_net.node.ip_addr.apply(lambda x: ip in x)
    if any(mask):
        node_idx = mask[mask==True].index[0]
        if node_idx is not None: 
            return ('node', node_idx)
    return None
    
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

def assign_ipaddr_to_elt(ict_net, elt, ip, netmask=None):
    # Handle ip lists (for routers) and convert cidr-style ip to ip and netmask
    if isinstance(ip, list):
        ipa = [IP_address(i) for i in ip]
        ip = [i.ip for i in ipa]
        if netmask is None:
            netmask = [i.netmask for i in ipa]
    else:
        ipa = IP_address(ip)
        ip = ipa.ip 
        if netmask is None: 
            netmask = ipa.netmask
            
    if elt[0]=='device':
        ict_net.device.at[elt[1],'ip_addr'] = ip
        ict_net.device.at[elt[1],'netmask'] = netmask
    elif elt[0]=='node':
        t = ict_net.node.iloc[elt[1]]['type']
        if t is not NodeType.ROUTER:
            raise UserWarning("Node_elt "+str(elt)+" is "+str(t)+", must be router-type node")
        else:
            ict_net.node.at[elt[1],'ip_addr'] = ip 
            ict_net.node.at[elt[1],'netmask'] = netmask
    else:
        raise UserWarning("Can't assign IP to "+str(elt[0])+" element, only node or device")
    return
    
        
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
            raise UserWarning("since end_ip is not used, start_ip must contain mask, using cidr notation") 
            return (False,None)           
    elif ip_range is not None: 
        cur_ip = IP_address(ip_range)
        last_ip = None  
        if cur_ip.netmask is None:
            raise UserWarning("ip_range must contain mask, using cidr notation")
            return (False,None)

    for e in eltlist:
        if not __check_elt_to_assign(ict_net, e):             
            continue        
        if e[0]=='node':
            ip_existing = ict_net[e[0]].at[e[1],'ip_addr']
            nm_existing = ict_net[e[0]].at[e[1],'netmask']
            if ip_existing is not None:
                ict_net[e[0]].at[e[1],'ip_addr'] += [cur_ip.ip]
                ict_net[e[0]].at[e[1],'netmask'] += [cur_ip.netmask]                
            else:
                ict_net[e[0]].at[e[1],'ip_addr'] = [cur_ip.ip]
                ict_net[e[0]].at[e[1],'netmask'] = [cur_ip.netmask]
        else:
            ict_net[e[0]].at[e[1],'ip_addr'] = cur_ip.ip
            ict_net[e[0]].at[e[1],'netmask'] = cur_ip.netmask
        inc_success = cur_ip.inc(own_network_only = (last_ip is None))         
        if (not inc_success) or (last_ip is not None and cur_ip.greater_than(last_ip)):
            return (e==eltlist[-1], None)
                
    return (True, cur_ip.ip) 


def __get_ip_addresses_from(ips: list, netmasks: list):
    '''
        Converts two lists containing ips and netmasks to one single list containing IP_address objects. 
        Input lists must have equal length. Single values (strings) may be used instead of lists, but the return value is always a list.        
    '''
    if not isinstance(ips, list): 
        ips = [ips]
    if not isinstance(netmasks, list): 
        netmasks = [netmasks]
    if len(ips)!=len(netmasks): 
        raise UserWarning("Input ips and netmasks lists must have equal length")
        return None
    ip_addresses = []
    for i in range(0,len(ips)):
        ip_addresses += [IP_address(ips[i], netmasks[i])]
    return ip_addresses
        

def __select_same_network(ip_list1: list, ip_list2: list):
    '''
        Selects ip addresses from lists that are in the same network
        Lists must be lists of IP_address objects
        Returns list of 2-tuple-sets
    ''' 
    same_network_pairs = [] 
    for ip1 in ip_list1: 
        for ip2 in ip_list2:
            if ip1.is_same_network(ip2):
                ip_pair = (ip1, ip2)
                if ip_pair not in same_network_pairs:
                    same_network_pairs += [ip_pair]
    return same_network_pairs

def update_iptables(ict_net, lup_table):
    '''
        Adds routing information from a luptable to involved nodes  
    '''
    
    for i,r in enumerate(lup_table):
        if 'hops' not in r.keys():
            raise UserWarning("LUP table must include hops for updating ip tables, please use include_hops=True")
            break
        if not r['delivering']:
            continue
        metric = 100-r['probability']*100
        # traverse hops
        destination = __get_ipaddr_by_element(ict_net, r['hops'][-1])
        for i in range(0, len(r['hops'])-1):
            e = r['hops'][i]
            if e[0]!="node": 
                continue
            # check if there is already static routing entry - if yes, continue
            iptables_static = ict_net.iptables[(ict_net.iptables.node_idx==e[1]) & (ict_net.iptables.destination==destination) & (ict_net.iptables.type=="static")]
            if not iptables_static.empty: 
                continue
            # fetch IP addresses at sender and gateway nodes that lie in the same network
            own_ip = __get_ipaddr_by_element(ict_net, e)
            own_netmask = __get_netmask_by_element(ict_net, e)
            own_ipaddr = __get_ip_addresses_from(own_ip, own_netmask)
            gateway_ip = __get_ipaddr_by_element(ict_net, r['hops'][i+1])
            gateway_netmask = __get_netmask_by_element(ict_net, r['hops'][i+1])
            gateway_ipaddr = __get_ip_addresses_from(gateway_ip, gateway_netmask)
            # TODO: add remove non-reachable gateways - otherwise this doesn't work in all cases, consider (conn 0) upstream 
            snips = __select_same_network(own_ipaddr, gateway_ipaddr) 
            if snips==[]:
                pilogger.warning("Nodes "+str(e)+" and "+str(r['hops'][i+1])+" are supposed to be connected but don't seem to share an IP network. Did you specify IP addresses and netmasks correctly?")
                continue
            elif len(snips)>1:
                pilogger.warning("Nodes "+str(e)+" and "+str(r['hops'][i+1])+" seem to share multiple IP networks. This may or may not be intended. Are you sure that IP addresses and netmasks are defined correctly?")
            (own_ip, gateway_ip) = snips[0] 
            entrycount = len(ict_net.iptables[ict_net.iptables["node_idx"]==e[1]])
            if not ict_net.iptables[(ict_net.iptables.node_idx==e[1]) & (ict_net.iptables.destination==destination)].empty:
                # iptable entry for this already exists 
                continue
            ientry = {"node_idx": e[1], 
              "entry": entrycount, 
              "destination": destination, 
              "netmask": gateway_netmask,
              "gateway": gateway_ip, 
              "link_idx": 0, 
              "type": "dynamic",
              "metric": metric}
            ict_net.iptables.loc[len(ict_net.iptables.index)] = ientry
        
    return
    
def get_iptable(ict_net, node_elt):
    '''
        Get routing table for node  
    '''
    if node_elt[0]!="node" or ict_net.node.iloc[node_elt[1]].type is not NodeType.ROUTER:
        return None
    iptable = ict_net.iptables[ict_net.iptables.node_idx==node_elt[1]].drop("node_idx", axis=1)
    iptable.set_index("entry")
    return iptable

def set_static_iptable_entry(ict_net, node_elt, destination, gateway, netmask = None, link_idx = None, metric = 0):
    '''
        Set static routing table entry for a node
        Note: function does not check for existence of destination and gateway ip. Use the inspect package to check this.
        
        destination and gateway must be non IP          
        gateway must be the IP of a node or device that node_elt is connected to
        if netmask is None, it is taken over from the node_elt
    '''
    
    if (node_elt[0]!="node" or node_elt[1] > len(ict_net.node)):
        raise UserWarning("Node_elt "+str(node_elt)+" is not a node or doesn't exist")
    t = ict_net.node.iloc[node_elt[1]]['type']
    if t is not NodeType.ROUTER:
        raise UserWarning("Node_elt "+str(node_elt)+" is "+str(t)+", must be router-type node")
    entrycount = len(ict_net.iptables[ict_net.iptables["node_idx"]==node_elt[1]])
    if link_idx is None:             
        # try to find link to destination and remember its type 
        ltype = None
        for l_idx in get_links_at(ict_net, node_elt):
            # Check if link connects our node with the gateway ip
            l = ict_net.link.iloc[l_idx] 
            to_ips = flatten2d([__get_ipaddr_by_element(ict_net, n) for n in l['to']])
            if ((node_elt in l['to']) and (__get_ipaddr_by_element(ict_net, l['from'])==gateway)) or \
                ((node_elt==l['from']) and (gateway in to_ips)):
                ltype = l['type']
            # Check if link directly connects our node to the destination
            elif destination==l['from'] or destination in to_ips:
                ltype = l['type']
        # try to find interface / link index by its type
        if ltype is not None: 
            try:
                link_idx = ict_net.node.iloc[node_elt[1]].link_types.index(ltype)
            except:
                link_idx = None        
    try:
        if netmask is None: 
            netmask = ict_net.node.iloc[node_elt[1]]['netmask'][link_idx]
    except:
        netmask=None
        
    ientry = {"node_idx": node_elt[1], 
              "entry": entrycount, 
              "destination": destination, 
              "netmask": netmask,
              "gateway": gateway, 
              "link_idx": link_idx, 
              "type": "static",
              "metric": metric}
    
    ict_net.iptables.loc[len(ict_net.iptables.index)] = ientry
     
    return 
