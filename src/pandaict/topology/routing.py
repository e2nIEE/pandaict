'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

import pandas as pd
import networkx as nx
import uuid
from pandaict.utils.utils import uuid2elt, get_elts_any
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt
from pandaict.topology.lup_table import LUP_table
from pandaict.utils.enums import RoutingType


def __get_pilinks(ict_net, mdg, routes):
    pilinks = []
    for i in range(0,len(routes)-1):
        edges = mdg.get_edge_data(routes[i], routes[i+1])        
        edge_lowest = None 
        from_pinode = mdg.nodes.get(routes[i])['pielt']
        to_pinode   = mdg.nodes.get(routes[i+1])['pielt']
        weight_lowest = None
        for key, e in edges.items():
            if weight_lowest is None or e['weight'] < weight_lowest:
                edge_lowest = e['pielt']
                weight_lowest = e['weight']        
        
        if edge_lowest[0] != "link": 
            raise UserWarning("Internal error: calculated link is invalid - pielt type does not fit")
        
        if from_pinode == ict_net.link.iloc[edge_lowest[1]]['from'] and to_pinode in ict_net.link.iloc[edge_lowest[1]]['to']:
            pilinks += [{'link': edge_lowest[1], 'downstream': True}]
        elif from_pinode in ict_net.link.iloc[edge_lowest[1]]['to'] and to_pinode == ict_net.link.iloc[edge_lowest[1]]['from']:
            pilinks += [{'link': edge_lowest[1], 'downstream': False}]
        else:
            raise UserWarning("Internal error: calculated link is invalid")
    return pilinks

def _calc_lup_table_lowest_latency(ict_net, conn_elt):
                    
    lup_table = LUP_table(ict_net, conn_elt)
    conn = lup_table.conn
    # create nxgraph for connection and get routes        
    mdg = create_multidigraph(ict_net, conn['protocol'], weights="latency", validate=True)
    from_dev = ('device', ict_net.app.iloc[conn['from']]['device'])
    to_dev = ('device', ict_net.app.iloc[conn['to']]['device'])
    from_nxnode = __get_nx_node_for_elt(mdg, from_dev)
    to_nxnode = __get_nx_node_for_elt(mdg, to_dev)
    droutes = nx.shortest_path(mdg, source=from_nxnode, target=to_nxnode, weight='weight')
    uroutes = nx.shortest_path(mdg, source=to_nxnode, target=from_nxnode, weight='weight')        
    
    pidlinks = __get_pilinks(ict_net, mdg, droutes)
    piulinks = __get_pilinks(ict_net, mdg, uroutes)    
    lup_table.add_route(downstream=True, delivering=True, probability=1.0, links=pidlinks)
    lup_table.add_route(downstream=False, delivering=True, probability=1.0, links=piulinks)
        
    return lup_table

def calc_lup_table(ict_net, conn_elt, routing_type):
    """
    Calculate link usage probability table.
    NOTE: currently only RoutingType.LOWEST_TOTAL_LATENCY supported 

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **conn_elt** (tuple or uuid) - id of connection element to calculate the lup table for
        
        **routing_type** - The routing type to use for the calculation. Use a RoutingType enum.
                            
    :OUTPUT:
        **lup_table** (LUP_table) - Link usage probability table 

    :EXAMPLE:
        calc_lup_table(ict_net, ('conn',2), RoutingType.LOWEST_TOTAL_LATENCY)
    """
    if routing_type == RoutingType.LOWEST_TOTAL_LATENCY:
        return _calc_lup_table_lowest_latency(ict_net, conn_elt)
    

def _get_info_item_package_size_byte(ict_net, info_item_type, protocol):
    
    pt = ict_net['std_types']['protocol'][protocol]
    pack_size = pt['base_package_size_byte']
    if info_item_type in pt['info_items'] and 'payload_size_byte' in pt.keys():
        idx = pt['info_items'].index(info_item_type)
        pack_size += pt['payload_size_byte'][idx]
    
    return pack_size
    
def _get_total_bandwidth_conn_Mbps(ict_net, conn, downstream):
    
    totbw = 0
    if not conn.in_service:
        return 0
    for i in range(0,len(conn.info_items)): 
        if downstream and conn.producer[i]==1 or not downstream and conn.producer[i]==0: 
            continue
        if conn.prod_freq_ms[i] is None or conn.prod_freq_ms[i]<0:
            continue
        ii = conn.info_items[i]
        iibw = (_get_info_item_package_size_byte(ict_net, ii, conn.protocol)*8/1E6) / (conn.prod_freq_ms[i]/1000)
        totbw += iibw
    
    return totbw
        
def calc_conn_bandwidth_Mbps(ict_net, conn_elt):
    """
    Calculate total bandwidth used by a connection, in Mbps.     

    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **conn_elt** (tuple or uuid) - id of connection element to calculate the bandwidth for
                                
    :OUTPUT:
        **(tot_bw_down, tot_bw_up)** (tuple) - Bandwith used by the connection in its downstream and upstream direction  

    :EXAMPLE:
        calc_conn_bandwidth_Mbps(ict_net, ('conn',2))
    """        
    conn = get_elts_any(ict_net, conn_elt, expected=['conn'])
    tot_bw_down = _get_total_bandwidth_conn_Mbps(ict_net, conn, True)
    tot_bw_up   = _get_total_bandwidth_conn_Mbps(ict_net, conn, False)
    return (tot_bw_down, tot_bw_up)

def calc_link_bandwidth_Mbps(ict_net, lup_table):
    """
    Calculate link bandwidths resulting from a specific link usage probability.  
    The latter needs to be given as lup table which was calculated for a specific connection. 
    To be used in conjunction with calc_lup_table to calculate link bandwidths for a given connection and routing method. 
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network         
            
        **lup_table** (LUP_table) - lup table for a connection in ict_net
                                
    :OUTPUT:
        **link_bw** (dict) - dict with link ids as keys and tuples as items. The tuples give the calculated used link bandwidth \
            in (downstream,upstream) directions  

    :EXAMPLE:
        .. highlight:: python
        .. code-block:: python
        
            ict_net = self.create_testnet3()
            lup_table = calc_lup_table(ict_net, ('conn', 1), RoutingType.LOWEST_TOTAL_LATENCY)
            link_bw   = calc_link_bandwidth_Mbps(ict_net, lup_table)
    """                      
    return add_link_bandwidth_Mbps(ict_net, {}, lup_table)    

def add_link_bandwidth_Mbps(ict_net, link_bw, lup_table):
    """
    Calculate link bandwidths resulting from a specific link usage probability, and add them up to already existing link bandwidths. 
    The latter needs to be given as lup table which was calculated for a specific connection. 
    To be used in conjunction with calc_lup_table to calculate link bandwidths for a given connection and routing method. 
    The add feature can be used to calculate the total link bandwidth usage for multiple connections by daisy-chaining       
    calc_lup_table and add_link_bandwidth_Mbps (see example below).
    
    :INPUT:
        **ict_net** (pandaictNet) - A pandaict network     

        **link_bw** (dict) - dict with link ids as keys and tuples as items. The tuples give the already used link bandwidth \
            in (downstream,upstream) directions 
            
        **lup_table** (LUP_table) - lup table for a connection in ict_net
                                
    :OUTPUT:
        **link_bw** (dict) - dict with link ids as keys and tuples as items. The tuples give the used link bandwidth after the calculation \
            in (downstream,upstream) directions  

    :EXAMPLE:
        .. highlight:: python
        .. code-block:: python
        
            ict_net = self.create_testnet3()
            link_bw = {}
            for i,_ in ict_net['conn'].iterrows():
                lup_table = calc_lup_table(ict_net, ('conn', i), RoutingType.LOWEST_TOTAL_LATENCY)
                link_bw   = add_link_bandwidth_Mbps(ict_net, link_bw, lup_table)
    """     
    # Calculate total data volume over timespan
    tot_bw_down, tot_bw_up = calc_conn_bandwidth_Mbps(ict_net, lup_table.conn_elt)    
    
    for r in lup_table:         
        p = r['probability']
        if r['downstream']: 
            plbw = p*tot_bw_down            
        else:            
            plbw = p*tot_bw_up
            
        for l in r['links']:
            lbw = link_bw.get(l['link'], [0,0]) # get existing link loading
            if l['downstream']: # link loaded in downstream direction
                lbw[0] += plbw               
            else: # link loaded in upstream direction                                    
                lbw[1] += plbw
            link_bw.update({l['link']: lbw})           
            
    return link_bw

# UNFINISHED / UNTESTED (RJ)
# def _get_total_volume_conn(conn, downstream, timespan_hours):
#
#     totvolume = 0
#
#     for i in range(0,len(conn.info_items)): 
#         if downstream and conn.producer[i]==1 or not downstream and conn.producer[i]==0: 
#             continue
#         if conn.prod_freq_ms[i] is None or conn.prod_freq_ms[i]<0:
#             continue
#         ii = conn.info_items[i]
#         ii_number = (timespan_hours*60*60*1000) / conn.prod_freq_ms[i] # Number of info items produced for timespan
#         ii_size = _get_info_item_package_size_byte(conn.info_items[i], conn.protocol)
#         totvolume += ii_number*ii_size
#
#     return totvolume
#
# def calc_link_volume_bytes(ict_net, lup_table, timespan_hours):
#
#     conn = ("conn", lup_table.conn_idx)
#     link_shares = {}  # shares of info items that use links, down/upstream
#     link_volumes = {} # data volumes adding up on links, down/upstream
#
#     # Calculate total data volume over timespan
#     tot_volume_down = _get_total_volume_conn(conn, True, timespan_hours)
#     tot_volume_up   = _get_total_volume_conn(conn, False, timespan_hours)
#
#     # DOWNSTREAM
#     for route in lup_table:
#         if not route.downstream or not route.delivering:
#             continue
#         for l in route.links: # for ex. [(4,True),(8,False),(2,True)]
#             share = link_shares.get(l[0], (0,0))
#             if l[1]: 
#                 share[0] += route.probability
#             else:
#                 share[1] += route.probability
#             link_shares.update({l[0]: share})
#
#     for l, ls in link_shares.items():
#         down_volume = ls[0]*tot_volume_down + (link_volumes.get(l, None)[0] or 0)
#         up_volume = ls[1]*tot_volume_down + (link_volumes.get(l, None)[1] or 0)                
#         link_volumes.update({l: (down_volume, up_volume)}) 
#
#     # UPSTREAM
#     # TODO: Add
#
#     return link_volumes