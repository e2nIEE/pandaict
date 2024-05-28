'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

import networkx as nx

import logging
logger = logging.getLogger("pandaICT_Core")

def _get_nx_node_for_elt(mdg, elt):
    node = [n for n in range(0,mdg.number_of_nodes()) if mdg.nodes[n]['pielt']==elt]
    if len(node)>1:
        logger.debug("_get_nx_node_for_elt found nodes "+str(node)+" sharing same pielt "+str(elt)+" - this shouldn't happen")
    if node is None or node==[]:
        return None
    else:
        return node[0]
    pass


def _validate_multidigraph(ict_net, mdg, protocol=None):
    
    passed = True
    # check edges
    for nxedge in enumerate(list(mdg.edges(data=True))):
        nxnode1  = nxedge[1][0]
        nxnode2  = nxedge[1][1]
        pinode1  = mdg.nodes[nxnode1]['pielt']
        pinode2  = mdg.nodes[nxnode2]['pielt']
        pilink   = nxedge[1][2]['pielt']
        if not pilink[0]=='link':
            logger.debug("_validate_multidigraph: found nxedge annotated with "+str(pilink)+", expected link element")
            passed = False
        else:
            pifrom = ict_net.link.iloc[pilink[1]]['from']
            pito = ict_net.link.iloc[pilink[1]]['to']            
            bw = ict_net.std_types['link'][ict_net.link.iloc[pilink[1]]['type']]['bandwidth_Mbps']
            if (isinstance(bw, float) or len(bw)<2 or bw[1]==0):
                bidir = False 
            else:
                bidir = True
            
            if not((pinode1==pifrom and pinode2 in pito) or (bidir and pinode2==pifrom and pinode1 in pito)):
                logger.debug("_validate_multidigraph: nxedge between nxnodes "+str(nxnode1)+" and "+str(nxnode2)+" does not match ict_net")
                passed = False
                
            if protocol is not None:
                if protocol not in ict_net.std_types['link'][ict_net.link.iloc[pilink[1]]['type']]['protocols']:
                    logger.debug("_validate_multidigraph: pandaICT link represented by nxedge between nxnodes "+ 
                                str(nxnode1)+" and "+str(nxnode2)+" does not support target protocol "+str(protocol))
                    passed = False  
        
    if not passed:
        logger.warn("_validate_multidigraph FAILED, check out reasons above if debuglevel DEBUG")
    return passed

def _create_multidigraph(ict_net, protocol, in_service_only = True, validate = False):
    
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
        
        # check directionality
        bw = ict_net.std_types['link'][l['type']]['bandwidth_Mbps']
        if (isinstance(bw, float) or len(bw)<2 or bw[1]==0):
            bidir = False 
        else:
            bidir = True
        
        # find nx nodes connected by the link
        from_elt = l['from']        
        to_elt = l['to']
        
        nxn1 = _get_nx_node_for_elt(mdg, from_elt)
        nxn2 = [_get_nx_node_for_elt(mdg, e) for e in to_elt]        
         
        for n2 in nxn2: 
            mdg.add_edge(nxn1, n2, pielt = ("link", i))            
            if bidir:
                mdg.add_edge(n2, nxn1, pielt = ("link", i))    
                
    if validate:
        passed = _validate_multidigraph(ict_net, mdg, protocol)
        if not passed:                        
            if not(logger.level==logging.DEBUG):
                print("Warning from _create_multidigraph: validation FAIL, set loglevel to debug and check the log")
            else:
                print("Warning from _create_multidigraph: validation fail, check the log")
    
    return mdg

def calc_routes_for_connection(ict_net, conn):
    pass
    
def calc_routes_between_devices(ict_net, conn, verbose=False):
    
    # Create the nxgraph
    mdg = _create_multidigraph(ict_net, conn['protocol'], validate=True)
    
    # Fetch devices used by the connection
    try:
        dev1 = ("device", ict_net.app.iloc[conn['from']]['device'])
    except:
        logger.debug("Failed to obtain from device for conn "+str(conn['name']))        
    try:
        dev2 = ("device", ict_net.app.iloc[conn['to']]['device'])
    except:
        logger.debug("Failed to obtain from device for conn "+str(conn['name']))
               
    # Fetch nynodes representing the devices
    n1 = _get_nx_node_for_elt(mdg, dev1)
    n2 = _get_nx_node_for_elt(mdg, dev2)
    if (n1 is None):
        logger.debug("_get_nx_node_for_elt failed for "+str(n1))
        return None 
    if (n2 is None):
        logger.debug("_get_nx_node_for_elt failed for "+str(n2))
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
    
    if verbose:            
        lhops = []
        for p in paths:
            hops = ""
            for elt in p:
                if elt[0]=='device':
                    hops += ict_net.device.iloc[elt[1]]['name']+"-"
                elif elt[0]=='node':
                    hops += ict_net.node.iloc[elt[1]]['name']+"-"
            hops = hops[:-1]
            lhops += [hops]            
        print("Paths for connection "+str(conn['name'])+" over "+str(conn['protocol'])+": "+str(lhops))
    return paths