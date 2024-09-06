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

#TODO check if MTBF/MTTR of devices is correctly respected

def _calc_MTBF_MTTR_serial2(mtbf_mttr1, mtbf_mttr2):    
    """
        Calculates MTBF and MTTR for a serial system with 2 subsystems 
        
        :OUTPUT:  
         **(MTBF, MTTR)** tuple - Total system MTBF and MTTR 
    
    """
    
    mtbf1 = mtbf_mttr1[0]
    mttr1 = mtbf_mttr1[1]
    mtbf2 = mtbf_mttr2[0]
    mttr2 = mtbf_mttr2[1]
        
    if mtbf1 == 0 and mtbf2 == 0:
        # can not calculate MTTR_total neither MTTR_total
        return (0,0)
    else:
        if mtbf1 == 0:
            return (mtbf2, mttr2)
        elif mtbf2 == 0:
            return (mtbf1, mttr1)
        else:
            MTBF_total = (mtbf1 * mtbf2) / (mtbf1 + mtbf2)
            if mttr1==0 or mttr2==0:
                MTTR_total = 0
            else:
                MTTR_total =  (mtbf1 * mttr2 + mtbf2 * mttr1) / (mtbf1 + mtbf2)        
            return (MTBF_total, MTTR_total)        

def _check_calc_MTBF_MTTR_route(ict_net, links):
    if not isinstance(links, list) or len(links)<2: 
        pilogger.warn("calc_MTBF_MTTR_route parameter must be list with at least 2 entries")
        return False
    for li in links:
        l = get_elts_any(ict_net, li)
        if isinstance(l['to'], list) and len(l['to'])>1: 
            pilogger.warn("calc_MTBF_MTTR_route currently doesn't support routes with multicast")
            return False
    lf = get_elts_any(ict_net, links[0]) # first link
    ll = get_elts_any(ict_net, links[-1]) # last link
    if not (lf['from'][0]=="device" or lf['to'][0][0]=="device") or not (ll['from'][0]=="device" or ll['to'][0][0]=="device"):
        pilogger.warn("calc_MTBF_MTTR_route first and last link must be connected to devices")
        return False
    return True


def calc_MTBF_route(ict_net, links):
    """
    Calculate MTBF along a route given by a list of links.    
    Links and nodes along the route are handled as a serial system and total MTBF is calculated accordingly.  
    Note: the link list may be obtained from a LUP table calculation.
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **links** (list of tuple) - list of links that define the route, in pandaICT element notation            
                            
    :OUTPUT:
        **MTBF_total** (float) - MTBF of serial system consisting of links and nodes along the route 

    :EXAMPLE:
        calc_MTBF_route(ict_net, [('link',1),('link',8),('link',0)])
    """
    if not _check_calc_MTBF_MTTR_route(ict_net, links):
        return None
           
    MTBF_route = 0   
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
        mtbf_link = get_values_for_links(ict_net, links[li], 'mtbf')[0][0]
        mtbf_node = nn['mtbf_h']
        
        if li==len(links)-1: # last link in the chain
            # add only link 
            if mtbf_link is not None and mtbf_link != 0:
                MTBF_route += 1/mtbf_link
            break
        else: # update total  MTBF and MTTR
            if mtbf_link is not None and mtbf_link != 0:
                MTBF_route += 1/mtbf_link
            if mtbf_node is not None and mtbf_node != 0:
                MTBF_route += 1/mtbf_node
        
        lni = nni
    
    # finally inverse 
    MTBF_route = 1/MTBF_route
    return MTBF_route

def calc_MTBF_MTTR_route(ict_net, links):
    """
    Calculate MTBF and MTTR along a route given by a list of links.    
    Links and nodes along the route are handled as a serial system and total MTBF and MTTR are calculated accordingly.  
    Note: the link list may be obtained from a LUP table calculation.
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **links** (list of tuple) - list of links that define the route, in pandaICT element notation            
                            
    :OUTPUT:
        **(MTBF_total, MTTR_total)** (tuple of float) - MTBF and MTBR of serial system consisting of links and nodes along the route 

    :EXAMPLE:
        calc_MTBF_MTTR_route(ict_net, [('link',1),('link',8),('link',0)])
    """
    if not _check_calc_MTBF_MTTR_route(ict_net, links):
        return None
           
    MTBF_route = None
    MTTR_route = None
    lni  = None # last node index
    
    for li in range(0,len(links)):
        l = get_elts_any(ict_net, links[li])
        if l['from'][0]=="device" or l['from']==lni:            
            nni = l['to'] # next node      
            if isinstance(nni, list):
                nni = nni[0]       
        else:            
            nni = l['from']
                    
        # get mtbfs, mttrs 
        mtbf_link = get_values_for_links(ict_net, links[li], 'mtbf')[0][0]
        mttr_link = get_values_for_links(ict_net, links[li], 'mttr')[0][0]            
        
        if li==len(links)-1: # last link in the chain
            # add only link 
            (MTBF_route, MTTR_route) = _calc_MTBF_MTTR_serial2((MTBF_route, MTTR_route), (mtbf_link, mttr_link))
            break
        else: # update total  MTBF and MTTR                                
            nn = get_elts_any(ict_net, nni)
            mtbf_node = nn['mtbf_h']
            mttr_node = nn['mttr_h'] 
            
            if li==0:
                # initialize
                (MTBF_route, MTTR_route) = _calc_MTBF_MTTR_serial2((mtbf_link, mttr_link), (mtbf_node, mttr_node))
            else:
                # add link and node subsequentially
                (MTBF_route, MTTR_route) = _calc_MTBF_MTTR_serial2((MTBF_route, MTTR_route), (mtbf_link, mttr_link))
                (MTBF_route, MTTR_route) = _calc_MTBF_MTTR_serial2((MTBF_route, MTTR_route), (mtbf_node, mttr_node))
                    
        lni = nni
    
    return (MTBF_route, MTTR_route)

def calc_MTBF_MTTR_by_lup(ict_net, lup_table, downstream=True):
    """
    Calculate MTBF and MTTR for a lup table, which represents a routing scheme for a connection.    
    Links and nodes along the route are handled as a serial system and total MTBF and MTTR are calculated accordingly.
    NOTE: this does not work for any routing algorithm which involves implicit or explicit copying information items in the network. 
    Examples for this are FLOODING or radio networks with multicast transmission.       
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **lup_table** (LUPtable) - LUP table previously calculated for a connection
        
        **downstream** (boolean) - output is calculated for the downstream direction on connection level if True, upstream if False            
                            
    :OUTPUT:
        **(MTBF_conn_total, MTTR_conn_total)** (tuple of float) - total MTBF and MTBR  

    :EXAMPLE:
        Note: this calculates the total MTBF and MTTR for connection id 1 in the upstream direction.
        
        lup_table = calc_lup_table(ict_net, ('conn', 1), RoutingType.LOWEST_TOTAL_LATENCY)
        calc_MTBF_MTTR_by_lup(ict_net, lup_table, downstream=False)
    """
    
    MTBF_conn_total = 0
    MTTR_conn_total = 0
    
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
        (MTBF_route, MTTR_route) = calc_MTBF_MTTR_route(ict_net, links)
        
        MTBF_conn_total += r['probability'] * MTBF_route
        MTTR_conn_total += r['probability'] * MTTR_route
        
    return (MTBF_conn_total, MTTR_conn_total)
    