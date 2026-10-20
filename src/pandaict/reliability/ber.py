'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.reliability.reliability_utils import __get_next_hop, __check_calc_route, __check_lup_prob_sum_lt_one
from pandaict.utils.enums import RoutingType, SortType
from pandaict.pilogger import pilogger
     
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
    if not __check_calc_route(ict_net, links, "calc_ber_route"):
        return None
           
    ber_route = 1   
    lni  = None # last node index
    
    for li in range(0,len(links)):

        l = get_elts_any(ict_net, links[li])
        nn, nni = __get_next_hop(ict_net, l, lni)
        
        # get mtbfs, mttrs 
        ber_link = get_values_for_links(ict_net, links[li], 'ber')[0][0]
        ber_node = nn.get('ber', None)
        
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
    NOTE: this does currently **not** work for any routing algorithm which involves implicit or explicit copying of information items in the network. 
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
    if not __check_lup_prob_sum_lt_one(lup_table, downstream):
        return None
    
    for r in lup_table: # iterate all routes 
        if r['downstream']!=downstream:
            continue 
        links = [('link', l['link']) for l in r['links']] 
        ber_route = calc_ber_route(ict_net, links)
        
        ber_conn_total += r['probability'] * ber_route        
        
    return ber_conn_total
    