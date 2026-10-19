'''
Created on 30.01.2024
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause

'''

from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.reliability.reliability_utils import __get_next_hop, __check_calc_route, __get_end_devices_route, __check_lup_prob_sum_lt_one
from pandaict.utils.enums import RoutingType, SortType
from pandaict.pilogger import pilogger
import math

def __all_nonzero_float(values):
    if isinstance(values, list):
        for v in values:
            if v is None or math.isnan(v) or v==0: 
                return False 
    else: 
        if values is None or math.isnan(values) or values==0: 
            return False
    return True

def __calc_mtbf_mttr_serial2(mtbf_mttr1, mtbf_mttr2):    
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
        # can not calculate mttr_total neither mttr_total
        return (0,0)
    else:
        if mtbf1 == 0:
            return (mtbf2, mttr2)
        elif mtbf2 == 0:
            return (mtbf1, mttr1)
        else:
            mtbf_total = (mtbf1 * mtbf2) / (mtbf1 + mtbf2)
            if mttr1==0 or mttr2==0:
                mttr_total = 0
            else:
                mttr_total =  (mtbf1 * mttr2 + mtbf2 * mttr1) / (mtbf1 + mtbf2)        
            return (mtbf_total, mttr_total)        

def _add_to_mtbf_route(ict_net, links, lni, mtbf_route, include_end_devices):
    for li in range(0,len(links)):
        l = get_elts_any(ict_net, links[li])
        nn, nni = __get_next_hop(ict_net, l, lni)
        
        # get mtbfs, mttrs 
        mtbf_link = get_values_for_links(ict_net, links[li], 'mtbf')[0][0]
        mtbf_node = nn['mtbf_h']
        
        if mtbf_link is not None and mtbf_link != 0:
            mtbf_route += 1/mtbf_link
        if li==len(links)-1: # last link in the chain                     
            if include_end_devices and __all_nonzero_float(mtbf_node):
                mtbf_route += 1/mtbf_node                
            break
        else: # update total  MTBF and MTTR, also add node        
            if __all_nonzero_float(mtbf_node):
                mtbf_route += 1/mtbf_node        
        lni = nni
    
    return lni, mtbf_route

def calc_mtbf_route(ict_net, links, include_end_devices = False):
    """
    Calculate MTBF along a route given by a list of links.    
    Links and nodes along the route are handled as a serial system and total MTBF is calculated accordingly.  
    Note: the link list may be obtained from a LUP table calculation.
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **links** (list of tuple) - list of links that define the route, in pandaict element notation. \
        First and last link must be connected to devices.             
                            
    :OPTIONAL:
        **include_end_devices** (boolean, default False) - If True, reliability of start and end device is also used. \
        If False, devices are neglected for the calculation.              
    
    :OUTPUT:
        **mtbf_total_h** (float) - MTBF of serial system consisting of links and nodes along the route, in hours 

    :EXAMPLE:
        calc_mtbf_route(ict_net, [('link',1),('link',8),('link',0)])
    """
    if not __check_calc_route(ict_net, links, "calc_mtbf_route"):
        return None
           
    mtbf_route = 0   
    lni  = None # last node index
    
    if include_end_devices:
        (start_dev, _) = __get_end_devices_route(ict_net, links)
        d = get_elts_any(ict_net, start_dev)
        if start_dev is not None and 'mtbf_h' in d.keys() and d['mtbf_h']!=0:
            mtbf_route += 1/d['mtbf_h']
                        
    lni, mtbf_route = _add_to_mtbf_route(ict_net, links, lni, mtbf_route, include_end_devices)
    
    # finally inverse 
    mtbf_route = 1/mtbf_route
    return mtbf_route

def _finalize_mtbf_mttr(li, mtbf_link, mttr_link, mtbf_node, mttr_node, mtbf_route, mttr_route, end_dev):
    if li==0: # only one link in chain
        (mtbf_route, mttr_route) = (mtbf_link, mttr_link)            
    else: # add link
        (mtbf_route, mttr_route) = __calc_mtbf_mttr_serial2((mtbf_route, mttr_route), (mtbf_link, mttr_link))
    if (end_dev is not None) and __all_nonzero_float(mtbf_node) and __all_nonzero_float(mttr_node):                
        (mtbf_route, mttr_route) = __calc_mtbf_mttr_serial2((mtbf_route, mttr_route), (mtbf_node, mttr_node))
    return mtbf_route, mttr_route

def _update_mtbf_mttr(mtbf_link, mttr_link, mtbf_node, mttr_node, mtbf_route, mttr_route):
    if mtbf_route==None and mttr_route==None:
        # initialize
        (mtbf_route, mttr_route) = __calc_mtbf_mttr_serial2((mtbf_link, mttr_link), (mtbf_node, mttr_node))
    else:
        # add link and node subsequentially
        (mtbf_route, mttr_route) = __calc_mtbf_mttr_serial2((mtbf_route, mttr_route), (mtbf_link, mttr_link))
        (mtbf_route, mttr_route) = __calc_mtbf_mttr_serial2((mtbf_route, mttr_route), (mtbf_node, mttr_node))
    return mtbf_route, mttr_route

def _handle_include_end_devices(ict_net, links, include_end_devices):
    if include_end_devices:
        (start_dev, end_dev) = __get_end_devices_route(ict_net, links)
        d = get_elts_any(ict_net, start_dev)
        if start_dev is not None:
            if 'mtbf_h' in d.keys() and d['mtbf_h']!=0:
                mtbf_route = d['mtbf_h']
            if 'mttr_h' in d.keys() and d['mttr_h']!=0:
                mttr_route = d['mttr_h']        
    else:
        mtbf_route = None
        mttr_route = None
        end_dev    = None
        
    return mtbf_route, mttr_route, end_dev

def calc_mtbf_mttr_route(ict_net, links, include_end_devices=False):
    """
    Calculate MTBF and MTTR along a route given by a list of links.    
    Links and nodes along the route are handled as a serial system and total MTBF and MTTR are calculated accordingly.  
    Note: the link list may be obtained from a LUP table calculation.
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **links** (list of tuple) - list of links that define the route, in pandaict element notation. \
        First and last link must be connected to devices.             

    :OPTIONAL:
        **include_end_devices** (boolean, default False) - If True, reliability of start and end device is also used. \
        If False, devices are neglected for the calculation.    
                            
    :OUTPUT:
        **(mtbf_total_h, mttr_total_h)** (tuple of float) - MTBF and MTTR of serial system consisting of links and nodes along the route, in hours 

    :EXAMPLE:
        calc_mtbf_mttr_route(ict_net, [('link',1),('link',8),('link',0)])
    """    
    
    if not __check_calc_route(ict_net, links, "calc_mtbf_mttr_route"):
        return None
               
    lni  = None # last node index
    
    mtbf_route, mttr_route, end_dev = _handle_include_end_devices(ict_net, links, include_end_devices)
    
    for li in range(0,len(links)):
        l = get_elts_any(ict_net, links[li])
        nn, nni = __get_next_hop(ict_net, l, lni)
                    
        # get mtbfs, mttrs 
        mtbf_link = get_values_for_links(ict_net, links[li], 'mtbf')[0][0]
        mttr_link = get_values_for_links(ict_net, links[li], 'mttr')[0][0]            
        mtbf_node = nn['mtbf_h']
        mttr_node = nn['mttr_h']
            
        if li==len(links)-1: # last link in the chain
            (mtbf_route, mttr_route) = _finalize_mtbf_mttr(li, mtbf_link, mttr_link, mtbf_node, mttr_node, 
                                                                mtbf_route, mttr_route, end_dev)
           
            break
        else: # update total  MTBF and MTTR                                                        
            (mtbf_route, mttr_route) = _update_mtbf_mttr(mtbf_link, mttr_link, mtbf_node, mttr_node, mtbf_route, mttr_route)            
                    
        lni = nni
    
    return (mtbf_route, mttr_route)

def calc_mtbf_mttr_by_lup(ict_net, lup_table, downstream=True, include_end_devices=False):
    """
    Calculate MTBF and MTTR for a lup table, which represents a routing scheme for a connection.    
    Links and nodes along the route are handled as a serial system and total MTBF and MTTR are calculated accordingly.
    NOTE: this does currently **not** work for any routing algorithm which involves implicit or explicit copying of information items in the network. 
    Examples for this are FLOODING or radio networks with multicast transmission.       
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **lup_table** (LUPtable) - LUP table previously calculated for a connection
        
        **downstream** (boolean) - output is calculated for the downstream direction on connection level if True, upstream if False            
                            
    :OPTIONAL:
        **include_end_devices** (boolean, default False) - If True, reliability of start and end device is also used. \
        If False, devices are neglected for the calculation.
    
    :OUTPUT:
        **(mtbf_conn_total_h, mttr_conn_total_h)** (tuple of float) - total MTBF and MTTR, in hours  

    :EXAMPLE:
        Note: this calculates the total MTBF and MTTR for connection id 1 in the upstream direction.
        
        lup_table = calc_lup_table(ict_net, ('conn', 1), RoutingType.LOWEST_TOTAL_LATENCY)
        calc_mtbf_mttr_by_lup(ict_net, lup_table, downstream=False)
    """
    
    mtbf_conn_total = 0
    mttr_conn_total = 0
    
    # Check requirement: lup probabilities must not add up to more than 1.0
    if not __check_lup_prob_sum_lt_one(lup_table, downstream):
        return None
    
    for r in lup_table: # iterate all routes 
        if r['downstream']!=downstream:
            continue 
        links = [('link', l['link']) for l in r['links']] 
        (mtbf_route, mttr_route) = calc_mtbf_mttr_route(ict_net, links, include_end_devices=include_end_devices)
        
        mtbf_conn_total += r['probability'] * mtbf_route
        mttr_conn_total += r['probability'] * mttr_route
        
    return (mtbf_conn_total, mttr_conn_total)
    