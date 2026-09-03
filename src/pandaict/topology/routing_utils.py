'''
Created on 30.01.2024
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

import networkx as nx
from pandaict.utils.utils import is_bidirectional, get_supported_protocols, get_elt
from pandaict.utils.enums import RoutingType
from pandaict.pilogger import pilogger

def __get_nx_node_for_elt(mdg, elt):
    node = [n for n in range(0,mdg.number_of_nodes()) if mdg.nodes[n]['pielt']==elt]
    if len(node)>1:
        pilogger.debug("__get_nx_node_for_elt found nodes "+str(node)+" sharing same pielt "+str(elt)+" - this shouldn't happen")
    if node==[]:
        return None
    else:
        return node[0]


def __log_debug_and_return_false(debugstr):
    pilogger.debug(debugstr)
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
            pifrom = ict_net.link.loc[pilink[1]]['from']
            pito = ict_net.link.loc[pilink[1]]['to']                            
            
            if not((pinode1==pifrom and pinode2 in pito) or (is_bidirectional(ict_net, pilink) and pinode2==pifrom and pinode1 in pito)):
                passed = __log_debug_and_return_false("__validate_multidigraph: nxedge between nxnodes "+str(nxnode1)+" and "+str(nxnode2)+" does not match ict_net")                
                
            if protocol is not None:
                if protocol not in get_supported_protocols(ict_net, pilink):
                    passed = __log_debug_and_return_false("__validate_multidigraph: pandaICT link represented by nxedge between nxnodes "+ 
                                str(nxnode1)+" and "+str(nxnode2)+" does not support target protocol "+str(protocol))                    
        
    __print_failed(passed)
    
    return passed

def __print_failed(passed):
    if not passed:
        if pilogger.level != logging.DEBUG:
            print("__validate_multidigraph FAILED, set loglevel to debug and check the log")
        else:
            print("__validate_multidigraph FAILED, check the log")

def __get_weight(ict_net, link, wtype):
    
    ltype = ict_net.std_types['link'][link['type']]
    if wtype=="latency":
        lty = ltype['latency_ms']
        if isinstance(lty, tuple):
            return lty
        elif lty is not None: 
            return (lty, lty)
        else:
            return None
    elif wtype=="length":
        return (link['length'],link['length']) if 'length' in link.keys() else None
    elif wtype=="bit_error_rate":
        if ('length' in link.keys()) and ('ber_per_km' in ltype.keys()):
            return (ltype['ber_per_km'] * link['length'], ltype['ber_per_km'] * link['length'])
        else:
            return None

def __mdg_add_elts(ict_net, mdg, elt_type, in_service_only, idx):
    # elt_type: "node" or "device"
    for i, n in ict_net[elt_type].iterrows():        
        if (in_service_only and n['in_service']) or not in_service_only:
            mdg.add_node(idx, pielt=(elt_type, i))
            idx+=1
    return idx
    
def __add_edges_to_multidigraph(mdg, nxn1, nxn2, weight, bidir, pielt):
    for n2 in nxn2:
        if n2 is None: 
            continue     
        mdg.add_edge(nxn1, n2, pielt = pielt, weight = weight[0] if weight is not None else None)            
        if bidir:
            mdg.add_edge(n2, nxn1, pielt = pielt, weight = weight[1] if weight is not None else None)
            
def create_multidigraph(ict_net, protocol, in_service_only = True, weights = None, validate = False):
    
    mdg = nx.MultiDiGraph()
    
    # Add devices and nodes as nodes
    idx = 0 
    idx = __mdg_add_elts(ict_net, mdg, "node", in_service_only, idx)
    idx = __mdg_add_elts(ict_net, mdg, "device", in_service_only, idx)
                
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
        if nxn1 is None: 
            continue
        nxn2 = [__get_nx_node_for_elt(mdg, e) for e in to_elt]                 
        __add_edges_to_multidigraph(mdg, nxn1, nxn2, weight, bidir=is_bidirectional(ict_net, ("link", i)), pielt=("link", i))
                
    if validate:
        __validate_multidigraph(ict_net, mdg, protocol)        
    
    return mdg

def __print_paths(ict_net, conn, paths):
    lhops = []
    for p in paths:
        hops = ""
        for elt in p['path']:
            if elt[0] in ['device','node']:
                hops += get_elt(ict_net,elt)['name'] + "-"
                        
        hops = hops[:-1]
        lhops += [p['direction'] + ": " +hops]
    
    print("Paths for connection " + str(conn['name']) + " over " + str(conn['protocol']) + ": " + str(lhops))


def __get_pict_paths(mdg, nfrom, nto):
    nxpaths = list(nx.all_simple_paths(mdg, source=nfrom, target=nto))
    if len(nxpaths)==0:
        return None
    paths = []
    for nxp in nxpaths:
        p = []
        for nxnode in nxp:            
            p += [mdg.nodes[nxnode]['pielt']]
        paths += [p] 
    return paths

def __get_end_nxnodes_for_conn(ict_net, mdg, conn):
    # Fetch devices used by the connection
    try:
        dev1 = ("device", ict_net.app.loc[conn['from']]['device'])
        dev2 = ("device", ict_net.app.loc[conn['to']]['device'])
    except (KeyError, IndexError, TypeError, AttributeError):
        pilogger.debug("Failed to obtain from or to device for conn "+str(conn['name']))        
            
    # Fetch nynodes representing the devices
    n1 = __get_nx_node_for_elt(mdg, dev1)
    n2 = __get_nx_node_for_elt(mdg, dev2)
    if (n1 is None or n2 is None):
        pilogger.debug("__get_nx_node_for_elt failed for "+str(dev1) if n1 is None else str(dev2))
        return None
    
    return n1,n2
    
def __get_possible_routes(ict_net, mdg, conn):
    
    n1, n2 = __get_end_nxnodes_for_conn(ict_net, mdg, conn)
    # Calculate paths between nxnodes and translate back to pandaICT elt representation
    nxpaths_down = __get_pict_paths(mdg, n1, n2)
    nxpaths_up   = __get_pict_paths(mdg, n2, n1)
    # differentiate bidirectional, up- and downstream paths 
    paths = []
    directions = []
    if nxpaths_down is not None:
        for p in nxpaths_down:
            if (nxpaths_up is not None) and (p in nxpaths_up or list(reversed(p)) in nxpaths_up):
                d = "bidirectional"
            else:
                d = "downstream"
            paths += [p]
            directions += [d]
    if nxpaths_up is not None:
        for p in nxpaths_up:
            if p in paths or list(reversed(p)) in paths: 
                continue
            else:             
                paths += [p]
                directions += ["upstream"]
        
    return [{'direction': directions[i], 'path': paths[i]} for i in range(0, len(paths))]