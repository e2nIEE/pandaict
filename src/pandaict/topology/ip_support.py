'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.08.2024

@author: jringelstein
'''

import pandas as pd
from pandaict.utils.utils import uuid2elt, get_elt, get_elts_any, to_elt, get_values_for_links, get_links_at, get_neighbour_elts, get_links_between
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __get_end_nxnodes_for_conn, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.topology.ip_address import IP_address
from pandaict.utils.enums import RoutingType, SortType, NodeType
from pandaict.pilogger import pilogger

pd.set_option("display.max_columns", 100)
pd.set_option('display.expand_frame_repr', False)


def init_extend_network(ict_net):    
    """
    Prepares extending existing pandaICT network by IP-specific information by adding additional data to nodes and devices \
        and adding a new data structure ("iptables") for the routing tables.  

    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network to be extended     
                            
    """ 
    ict_net.iptables = pd.DataFrame(columns=["node_idx", "entry", "destination", "netmask", "gateway", "link_idx", "type", "metric"])
    ict_net.device.insert(4, "ip_addr", [None]*len(ict_net.device))
    ict_net.device.insert(4, "netmask", [None]*len(ict_net.device))
    ict_net.node.insert(4, "ip_addr", [None]*len(ict_net.node))
    ict_net.node.insert(4, "netmask", [None]*len(ict_net.node))
    
    # Example: 
    # ict_net.iptable = {1: [{"dest": "192.168.0.1/24", "gateway": "192.168.0.1/24"}, {"dest": "default", "gateway": "192.168.0.1/24"}]}

def __get_ipaddr_by_element(ict_net, e):
    if e[0]=='device':
        return [ict_net.device.iloc[e[1]].ip_addr]
    elif e[0]=='node':
        return ict_net.node.iloc[e[1]].ip_addr
    else:
        return None
    
def __get_netmask_by_element(ict_net, e):
    if e[0]=='device':
        return [ict_net.device.iloc[e[1]].netmask]
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

def _convert_ip_netmask(ip, netmask):
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
    return ip, netmask

def _check_convert_assign_ipaddr_to_elt(elt, ip, netmask=None):
    if (elt[0]=='node' and not isinstance(ip, list)):
        raise UserWarning("IP for node-type element must be a list")
    
    # Handle ip lists (for routers) and convert cidr-style ip to ip and netmask    
    ip, netmask = _convert_ip_netmask(ip, netmask) 
            
    if (elt[0]=='node' and not isinstance(netmask, list)):
        raise UserWarning("Parameters must allow to derate a netmask list for node-type element. Please use CIDR notation or provide netmask as list.")
    if isinstance(ip, list) and (len(ip) != len(netmask)): 
        raise UserWarning("Got netmask list of different length than IP list. Please re-check parameters.")
    return ip, netmask                         
    

def assign_ipaddr_to_elt(ict_net, elt, ip, netmask=None):
    """
    Assign an IP address to a pandaict router-type node or device.

    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network
        
        **elt** ((string, int) tuple) - pandaict element identifier of a router-type node or device to assign the IP to.               
        
        **ip** (string or list of string) - IP(s) to assign to the element, in string representation. CIDR notation may be used. \
            Note: for router-type nodes, it is mandatory to use a list.      
    
    :OPTIONAL:                        
        **netmask** (string or list of string) - netmask(s) for IP(s). If used, this overrides CIDR notation in the addresses.
        
    :EXAMPLE:
        .. highlight:: python
        .. code-block:: python
        
            assign_ipaddr_to_elt(ict_net, ('device',1), ip="192.168.0.1", netmask="255.255.255.0")
            assign_ipaddr_to_elt(ict_net, ('node',2), ip=["10.2.2.0", "10.4.2.0"], netmask=["255.255.240.0", "255.255.240.0"])
            # Alternative equivalent to this:
            assign_ipaddr_to_elt(ict_net, ('node',2), ip=["10.2.2.0/20", "10.4.2.0/20"])
            
    Note: if a list is used for **ip**, a list of same length must also be used for **netmask**, otherwise a UserWarning is thrown. 
        
    """ 
    ip, netmask = _check_convert_assign_ipaddr_to_elt(elt, ip, netmask)
    
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
    
def _get_cur_last_ip(start_ip, end_ip, ip_range, netmask):
    if start_ip is not None:         
        cur_ip  = IP_address(start_ip)
        last_ip = None        
        if cur_ip.netmask is None and netmask is not None:
            cur_ip.netmask = netmask                
        if end_ip is not None: 
            last_ip  = IP_address(end_ip)
        elif cur_ip.netmask is None:
            raise UserWarning("since end_ip is not used, start_ip must contain mask, using cidr notation")                 
    elif ip_range is not None: 
        cur_ip = IP_address(ip_range)
        last_ip = None  
        if cur_ip.netmask is None:
            raise UserWarning("ip_range must contain mask, using cidr notation")
    return cur_ip, last_ip 
    
def assign_ipaddr_to_elts(ict_net, eltlist, start_ip=None, end_ip=None, netmask=None, ip_range=None):
    """
    Subsequently assigns IP addresses to nodes and devices in eltlist using given address range  
    Elements need to be router-type nodes or devices. Other element types are ignored. 
    The IP address range to be used can be given explicitly (start end end IP address) or using CIDR notation.
        
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **eltlist** (list of tuple) - list of elements in pandaICT elements notation. Elements other than devices or nodes are ignored.  
        
        **start_ip** (string) - IP to assign to the first element in eltlist. May use CIDR notation, where mask is used as netmask \
            overriding the netmask parameter. 
            
    :OPTIONAL:    
        **end_ip** (string) - Last IP in usable address range. May use CIDR notation but mask is ignored. Only respected \
            if start_ip is used. If start_ip contains a mask (cidr notation), end_ip is ignored but the ip range comprises \
            start_ip to the highest host ip in the same IP network
        
        **ip_range** (string) - Alternative option for IP address range. IP in CIDR notation. The address range comprises the whole IP subnet \
            indicated by this. E.g. ip_range=10.0.0.1/24 translates to start_ip=10.0.0.1, end_ip=10.0.0.254
            
        **netmask** (string) - Netmask, which is also assigned to elements. If start_ip is given in CIDR notation or ip_range is used, \
            this parameter will be ignored but instead the mask from start_ip/ip_range is used. 
                            
    :OUTPUT:
        **(complete, next_free_ip)** (boolean, string) - If complete is True, all elements in the list (except invalid ones) were assigned an IP. If False, \
            the IP address range was insufficient for that. next_free_ip is the next IP within the address range that was not assigned to an element. \
            It is None if the address range was fully used.    

    :EXAMPLE:
        .. highlight:: python
        .. code-block:: python
        
            assign_ipaddr_to_elts(ict_net, [('device',1),('node',4),('node',5)], start_ip="10.0.0.1", end_ip="10.0.0.1", netmask="255.255.255.0")
            # Alternative equivalent to this:
            assign_ipaddr_to_elts(ict_net, [('device',1),('node',4),('node',5)], ip_range="10.0.0.1/24")
             
    """
    cur_ip, last_ip = _get_cur_last_ip(start_ip, end_ip, ip_range, netmask)
            
    for e in eltlist:
        if not __check_elt_to_assign(ict_net, e):             
            continue        
        if e[0]=='node':
            ip_existing = ict_net[e[0]].at[e[1],'ip_addr']
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
    ip_addresses = []
    for i in range(0,len(ips)):
        ip_addresses += [IP_address(ips[i], netmasks[i])]
    return ip_addresses
        
def _get_neighbour_ips_and_ports(ict_net, ne, our_node, node_elt, neighbour_ips, ports):
    their_elt = get_elt(ict_net, ne)
    # get linktypes between us and neighbour        
    in_between_link_idxs = get_links_between(ict_net, node_elt, ne, respect_direction=True)
    in_between_linktypes = [ict_net.link.iloc[li]['type'] for li in in_between_link_idxs]
    # look at all our ip addresses        
    for i in range(0, len(our_node['ip_addr'])):
        # get our ip data for this address
        our_ip = IP_address(our_node['ip_addr'][i], our_node['netmask'][i])              
        our_linktype = our_node['link_types'][i]
        if our_linktype not in in_between_linktypes:
            continue
        # look at all ip addresses of neighbour and check if we are connected to them
        rend = len(their_elt['ip_addr']) if isinstance(their_elt['ip_addr'], list) else 1
        for j in range(0, rend):
            if ne[0]=='node':
                their_ip = IP_address(their_elt['ip_addr'][j], their_elt['netmask'][j])    
                their_linktype = their_elt['link_types'][j]
            else:
                their_ip = IP_address(their_elt['ip_addr'], their_elt['netmask'])
                their_linktype = our_linktype
            if our_linktype==their_linktype and our_ip.is_same_network(their_ip):
                # neighbour is reachable over this link and IP 
                neighbour_ips += [their_ip.ip]
                ports += [i]
    return neighbour_ips, ports        


def __get_neighbour_ips_respecting_ports(ict_net, node_elt):
    # fetch list of neighbour nodes    
    if node_elt[0]!="node":
        return None    
    neighbour_ips = []
    ports = []
    our_node = ict_net.node.iloc[node_elt[1]]
    neighbour_elts = get_neighbour_elts(ict_net, node_elt, respect_in_service=True) 
    for ne in neighbour_elts:         
        neighbour_ips, ports = _get_neighbour_ips_and_ports(ict_net, ne, our_node, node_elt, neighbour_ips, ports)                               
    return neighbour_ips, ports                
                    

def update_iptables(ict_net, lup_table):
    """
    Adds routing information from a lup table to a network's IP routing table.    

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **lup_table** (LUP_table) - link usage probability table table that is the result of a lup table calculation using routing.calc_lup_table. \
            Note: **include_hops=True** must be used for the lup table calculation, otherwise this won't work. Also, use **respect_iptables=True** \
            (default) to respect static IP routing table entries during the lup table calculation.                                       

    :EXAMPLE:
        .. highlight:: python
        .. code-block:: python
        
            lup_table = calc_lup_table(ict_net, ('conn', 0), RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True) 
            update_iptables(ict_net, lup_table)
        
    Note: there is no output to this, but **ict_net.iptable** is modified.
    """ 
    
    for _,r in enumerate(lup_table):
        if 'hops' not in r.keys():
            raise UserWarning("LUP table must include hops for updating ip tables, please use include_hops=True when calling routing.calc_lup_table")            
        if not r['delivering']:
            continue
        metric = 100-r['probability']*100
        # traverse hops
        destination = __get_ipaddr_by_element(ict_net, r['hops'][-1])[0]
        for i in range(0, len(r['hops'])-1):
            e = r['hops'][i]
            if e[0]!="node": 
                continue
            # check if there is already static routing entry - if yes, continue
            iptables_static = ict_net.iptables[(ict_net.iptables.node_idx==e[1]) & (ict_net.iptables.destination==destination) & (ict_net.iptables.type=="static")]
            if not iptables_static.empty: 
                continue
            # fetch IP addresses at sender and gateway nodes that lie in the same network
            (reachable_ips, ports) = __get_neighbour_ips_respecting_ports(ict_net, e)
            gateway_ips_all = __get_ipaddr_by_element(ict_net, r['hops'][i+1])
            gateway_ip = [ip for ip in gateway_ips_all if ip in reachable_ips]            
            if gateway_ip is None:
                pilogger.warning("Nodes "+str(e)+" and "+str(r['hops'][i+1])+" are supposed to be connected but don't seem to share an IP network. Did you specify IP addresses and netmasks correctly?")
                continue
            else:
                if len(gateway_ip) > 1:
                    pilogger.warning("Nodes "+str(e)+" and "+str(r['hops'][i+1])+" seem to share multiple IP networks. This may or may not be intended. Are you sure that IP addresses and netmasks are defined correctly?")            
                gateway_ip = gateway_ip[0]
                pidx = reachable_ips.index(gateway_ip) 
                link_idx = ports[pidx]
            gateway_netmasks_all = __get_netmask_by_element(ict_net, r['hops'][i+1])
            gateway_netmask = gateway_netmasks_all[gateway_ips_all.index(gateway_ip)]
                                
            entrycount = len(ict_net.iptables[ict_net.iptables["node_idx"]==e[1]])
            if not ict_net.iptables[(ict_net.iptables.node_idx==e[1]) & (ict_net.iptables.destination==destination)].empty:
                # iptable entry for this already exists 
                continue
            ientry = {"node_idx": e[1], "entry": entrycount, "destination": destination, "netmask": gateway_netmask, "gateway": gateway_ip, 
                      "link_idx": link_idx,"type": "dynamic", "metric": metric}
            ict_net.iptables.loc[len(ict_net.iptables.index)] = ientry
            
    
def get_iptable(ict_net, node_elt):
    """
    Fetch IP routing table entries for a router-type node.

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **node_elt** (str, int) -pandaict identifier of a node in ict_net
                            
    :OUTPUT:
        **iptable** (DataFrame) - The IP table of the node, or None if there are no IP table entries for this node. 

    :EXAMPLE:
        get_iptable(ict_net, ('node',2))
    """ 
    if node_elt[0]!="node" or ict_net.node.iloc[node_elt[1]].type is not NodeType.ROUTER:
        return None
    iptable = ict_net.iptables[ict_net.iptables.node_idx==node_elt[1]].drop("node_idx", axis=1)
    iptable.set_index("entry")
    return iptable

def __get_link_type_to_destination(ict_net, node_elt, gateway, destination):
    # TODO: review this, maybe needs checking if the link connects node and gateway within same network (if changed, adapt Sphinx).
    ltype = None
    for l_idx in get_links_at(ict_net, node_elt):
        # Check if link connects our node with the gateway ip
        l = ict_net.link.iloc[l_idx] 
        to_ips = [__get_ipaddr_by_element(ict_net, n) for n in l['to']]
        to_ips = [i for sub in to_ips for i in sub] # flatten 2D list
        if (node_elt in l['to'] and __get_ipaddr_by_element(ict_net, l['from'])==gateway) or \
            (node_elt==l['from'] and gateway in to_ips) or \
            (destination==l['from'] or destination in to_ips): # Link directly connects our node to the destination
            ltype = l['type']
    return ltype 

def set_static_iptable_entry(ict_net, node_elt, destination, gateway, netmask = None, link_idx = None, metric = 0):    
    """
    Set static IP routing table entry for a node.

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **node_elt** (str, int) -pandaict identifier of a node in ict_net
                            
    :OUTPUT:
        **iptable** (DataFrame) - The IP table of the node, or None if there are no IP table entries for this node. 

    :EXAMPLE:
        get_iptable(ict_net, ('node',2))
    
    Note: this function does not yet check if the gateway IP is in the same network as the node IP. \
        Also it does not check for existence of destination and gateway ip. Use the inspect package to check the latter.
    
    """
    if (node_elt[0]!="node" or node_elt[1] > len(ict_net.node)):
        raise UserWarning("Node_elt "+str(node_elt)+" is not a node or doesn't exist")
    t = ict_net.node.iloc[node_elt[1]]['type']
    if t is not NodeType.ROUTER:
        raise UserWarning("Node_elt "+str(node_elt)+" is "+str(t)+", must be router-type node")
    entrycount = len(ict_net.iptables[ict_net.iptables["node_idx"]==node_elt[1]])
    if link_idx is None:             
        # try to find link to destination and remember its type 
        ltype = __get_link_type_to_destination(ict_net, node_elt, gateway, destination)            
            
        # try to find interface / link index by its type
        if ltype is not None: 
            try:
                link_idx = ict_net.node.iloc[node_elt[1]].link_types.index(ltype)
            except (IndexError, KeyError, AttributeError, ValueError, TypeError):
                link_idx = None        
    try:
        if netmask is None: 
            netmask = ict_net.node.iloc[node_elt[1]]['netmask'][link_idx]
    except (IndexError, KeyError, AttributeError, ValueError, TypeError):
        netmask=None
        
    ientry = {"node_idx": node_elt[1], "entry": entrycount, "destination": destination, "netmask": netmask, "gateway": gateway, 
              "link_idx": link_idx, "type": "static", "metric": metric}    
    ict_net.iptables.loc[len(ict_net.iptables.index)] = ientry