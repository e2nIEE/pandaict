'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

import networkx as nx
from pandaict.utils.utils import is_bidirectional, get_supported_protocols, get_elt
from pandaict.utils.enums import RoutingType

import logging
logger = logging.getLogger("pandaICT_Core")

def __get_nx_node_for_elt(mdg, elt):
    node = [n for n in range(0,mdg.number_of_nodes()) if mdg.nodes[n]['pielt']==elt]
    if len(node)>1:
        logger.debug("__get_nx_node_for_elt found nodes "+str(node)+" sharing same pielt "+str(elt)+" - this shouldn't happen")
    if node==[]:
        return None
    else:
        return node[0]


def __log_debug_and_return_false(debugstr):
    logger.debug(debugstr)
    return False

def __validate_multidigraph(ict_net, mdg, protocol=None):
    
    passed = True
    # check edges
    for nxedge in enumerate(list(mdg.edges(data=True))):
        nxnode1  = nxedge[1][0]
        nxnode2  = nxedge[1][1]
        pinode1  = mdg.nodes[nxnode1]['pielt']
        pinode2  = mdg.nodes[nxnode2]['pielt']
        pilink   = nxedge[1][2]['pielt']
        if pilink[0] != 'link':
            passed = __log_debug_and_return_false("__validate_multidigraph: found nxedge annotated with "+str(pilink)+", expected link element")            
        else:
            pifrom = ict_net.link.iloc[pilink[1]]['from']
            pito = ict_net.link.iloc[pilink[1]]['to']                            
            
            if not((pinode1==pifrom and pinode2 in pito) or (is_bidirectional(ict_net, pilink) and pinode2==pifrom and pinode1 in pito)):
                passed = __log_debug_and_return_false("__validate_multidigraph: nxedge between nxnodes "+str(nxnode1)+" and "+str(nxnode2)+" does not match ict_net")                
                
            if protocol is not None:
                if protocol not in get_supported_protocols(ict_net, pilink):
                    passed = __log_debug_and_return_false("__validate_multidigraph: pandaICT link represented by nxedge between nxnodes "+ 
                                str(nxnode1)+" and "+str(nxnode2)+" does not support target protocol "+str(protocol))                    
        
    if not passed:        
        if logger.level != logging.DEBUG:
            print("__validate_multidigraph FAILED, set loglevel to debug and check the log")
        else:
            print("__validate_multidigraph FAILED, check the log")
    
    return passed

def __get_weight(ict_net, link, wtype):
    
    if wtype=="latency":
        lty = ict_net.std_types['link'][link['type']]['latency_ms']
        if isinstance(lty, tuple):
            return lty
        elif lty is not None: 
            return (lty, lty)
        else:
            return None
    elif wtype=="length":
        return (link['length'],link['length']) or None
    elif wtype=="bit_error_rate":        
        return (link['type']['ber_per_km'] * link['length'], link['type']['ber_per_km'] * link['length']) or None
    
def create_multidigraph(ict_net, protocol, in_service_only = True, weights = None, validate = False):
    
    mdg = nx.MultiDiGraph()
    
    # Add devices and nodes as nodes
    idx = 0 
    for i, n in ict_net.node.iterrows():        
        if (in_service_only and n['in_service']) or not in_service_only:
            mdg.add_node(idx, pielt=("node", i))
            idx+=1
    for i, d in ict_net.device.iterrows():
        if (in_service_only and d['in_service']) or not in_service_only:
            mdg.add_node(idx, pielt=("device", i))
            idx+=1        
    # Add edges
    idx = 0
    for i, l in ict_net.link.iterrows():
        # check protocol and in_service
        if protocol not in ict_net.std_types['link'][l['type']]['protocols'] or (in_service_only and not l['in_service']):
            continue                 
                                
        # find nx nodes connected by the link
        from_elt = l['from']        
        to_elt = l['to']
        weight = __get_weight(ict_net, l, weights)        
        nxn1 = __get_nx_node_for_elt(mdg, from_elt)
        nxn2 = [__get_nx_node_for_elt(mdg, e) for e in to_elt]                 
        for n2 in nxn2:             
            mdg.add_edge(nxn1, n2, pielt = ("link", i), weight = weight[0] or None)            
            if is_bidirectional(ict_net, ("link", i)):
                mdg.add_edge(n2, nxn1, pielt = ("link", i), weight = weight[1] or None)    
                
    if validate:
        __validate_multidigraph(ict_net, mdg, protocol)        
    
    return mdg

def __print_paths(ict_net, conn, paths):
    lhops = []
    for p in paths:
        hops = ""
        for elt in p:
            if elt[0] in ['device','node']:
                hops += get_elt(ict_net,elt)['name'] + "-"
                        
        hops = hops[:-1]
        lhops += [hops]
    
    print("Paths for connection " + str(conn['name']) + " over " + str(conn['protocol']) + ": " + str(lhops))


def __get_possible_routes(ict_net, mdg, conn):
    # Fetch devices used by the connection
    try:
        dev1 = ("device", ict_net.app.iloc[conn['from']]['device'])
        dev2 = ("device", ict_net.app.iloc[conn['to']]['device'])
    except:
        logger.debug("Failed to obtain from or to device for conn "+str(conn['name']))        
            
    # Fetch nynodes representing the devices
    n1 = __get_nx_node_for_elt(mdg, dev1)
    n2 = __get_nx_node_for_elt(mdg, dev2)
    if (n1 is None or n2 is None):
        logger.debug("__get_nx_node_for_elt failed for "+str(dev1) if n1 is None else str(dev2))
        return None
    
    # Calculate paths between nxnodes and translate back to pandaICT elt representation
    nxpaths = list(nx.all_simple_paths(mdg, source=n1, target=n2))
    if len(nxpaths)==0:
        return None
    paths = []
    for nxp in nxpaths:
        p = []
        for nxnode in nxp:            
            p += [mdg.nodes[nxnode]['pielt']]
        paths += [p] 
        
    return paths


def calc_routes_for_connection(ict_net, conn, verbose=False):
    """
        Calculates possible routes through the physical network for a given connection. 

        :INPUT:
            **ict_net** (dict) - The pandaict network
            
            **conn** (dataframe) - The connection element for which routes shall be calculated

        :OPTIONAL:
            **verbose** (boolean, default False) - If True, prints additional information about found paths. 
        
        :OUTPUT: 
            **routes** (2D list of (string, int)) - A list of possible paths through the network. The list is \
                two-dimensional (i,j), where each row (i) represents a single path, again consisting of a number \
                of pandaict devices or nodes. These are given in pandaict element notation and indicate the \
                "hops" that information items using the connection can take.  
        
        :EXAMPLE:
            calc_routes_for_connection(ict_net, ict_net.conn.iloc[0])

    """ 
    # Create the nxgraph
    mdg = create_multidigraph(ict_net, conn['protocol'], validate=True)
    
    paths = __get_possible_routes(ict_net, mdg, conn)
    
    if verbose:            
        __print_paths(ict_net, conn, paths)
        
    return paths



