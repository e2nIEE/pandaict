'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

import pandas as pd
import networkx as nx
import uuid
from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.utils.enums import RoutingType, SortType
from pandaict.pilogger import pilogger

def _check_calc_ber_route(ict_net, links):
    if not isinstance(links, list) or len(links)<2: 
        pilogger.warn("calc_ber_route parameter must be list with at least 2 entries")
        return False
    for li in links:
        l = get_elts_any(ict_net, li)
        if isinstance(l['to'], list) and len(l['to'])>1: 
            pilogger.warn("calc_ber_route currently doesn't support routes with multicast")
            return False
    lf = get_elts_any(ict_net, links[0]) # first link
    ll = get_elts_any(ict_net, links[-1]) # last link
    if not (lf['from'][0]=="device" or lf['to'][0][0]=="device") or not (ll['from'][0]=="device" or ll['to'][0][0]=="device"):
        pilogger.warn("calc_ber_route first and last link must be connected to devices")
        return False
    return True
    
def calc_ber_route(ict_net, links):
    """
    Calculate bit error rate (ber) along a route given by a list of links.    
    Links and nodes along the route are handled as a serial system and total ber is calculated accordingly.  
    Note: the link list may be obtained from a LUP table calculation.
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **links** (list of tuple) - list of links that define the route, in pandaICT element notation            
                            
    :OUTPUT:
        **ber_total** (float) - ber of serial system consisting of links and nodes along the route 

    :EXAMPLE:
        calc_ber_route(ict_net, [('link',1),('link',8),('link',0)])
    """
    if not _check_calc_ber_route(ict_net, links):
        return None
           
    ber_route = 1   
    lni  = None # last node index
    
    for li in range(0,len(links)):

        l = get_elts_any(ict_net, links[li])
        if l['from'][0]=="device" or l['from']==lni:            
            nni = l['to'] # next node  
            if isinstance(nni, list):
                nni = nni[0]           
        else:            
            nni = l['from']            
        nn = get_elts_any(ict_net, nni)
        
        # get mtbfs, mttrs 
        ber_link = get_values_for_links(ict_net, links[li], 'ber')[0][0]
        ber_node = nn['ber']
        
        if li==len(links)-1: # last link in the chain
            # add only link             
            if ber_link is not None:
                ber_route *= 1-ber_link
            break            
        else: # update total  MTBF and MTTR
            if ber_link is not None:
                ber_route *= 1-ber_link
            if ber_node is not None:
                ber_route *= 1-ber_node
        
        lni = nni
    
    # finally inverse 
    ber_route = 1-ber_route
    return ber_route

def calc_ber_by_lup(ict_net, lup_table, downstream=True):
    """
    Calculate bit error rate (ber) for a lup table, which represents a routing scheme for a connection.    
    Links and nodes along the route are handled as a serial system and total ber is calculated accordingly.
    NOTE: this does not work for any routing algorithm which involves implicit or explicit copying information items in the network. 
    Examples for this are FLOODING or radio networks with multicast transmission.       
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **lup_table** (LUPtable) - LUP table previously calculated for a connection
        
        **downstream** (boolean) - output is calculated for the downstream direction on connection level if True, upstream if False            
                            
    :OUTPUT:
        **ber_total** (float) - total ber  

    :EXAMPLE:
        Note: this calculates the total ber for connection id 1 in the upstream direction.
        
        lup_table = calc_lup_table(ict_net, ('conn', 1), RoutingType.LOWEST_TOTAL_LATENCY)
        calc_ber_by_lup(ict_net, lup_table, downstream=False)
    """
    
    ber_conn_total = 0
    
    # Check requirement: lup probabilities must not add up to more than 1.0
    pr_sum = 0    
    for r in lup_table:
        if r['downstream']!=downstream:
            continue
        pr_sum += r['probability']
    if pr_sum > 1.0:
        pilogger.warn("calc_MTBF_MTTR_by_lup: lup table probabilities add up to "+str(pr_sum)+", maximal supported: 1.0")
        return None
    
    for r in lup_table: # iterate all routes 
        if r['downstream']!=downstream:
            continue 
        links = [('link', l['link']) for l in r['links']] 
        ber_route = calc_ber_route(ict_net, links)
        
        ber_conn_total += r['probability'] * ber_route        
        
    return ber_conn_total
    