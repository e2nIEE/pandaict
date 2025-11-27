'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 20.11.2025

@author: fnuetz, jringelstein
'''


# from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
# from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __print_paths
# from pandaict.topology.lup_table import LUP_table
# from pandaict.reliability.reliability_utils import __get_next_hop, __check_calc_route, __check_lup_prob_sum_lt_one
# from pandaict.utils.enums import RoutingType, SortType
# from pandaict.pilogger import pilogger

import math
import numpy as np
import networkx as nx
import random
import statistics  
   
#----------------------------------------------------------------------------------------------------------------------
# Helper: update the graph based on current edge states
# ----------------------------------------------------------------------------------------------------------------------
def active_subgraph(G, edge_state, node_state):
    """
    Return subgraph of G containing only the edges which are marked as UP in 'state' and whose adjacent nodes are UP.

    :INPUT:
        **G**           - networkx.Graph, original graph
        **edge_state**  - dict, edge status {edge: 0/1}, with 1 = UP, 0 = DOWN.
        **node_state**  - dict, node status {edge: 0/1}, with 1 = UP, 0 = DOWN.

    :OUTPUT:
        **H**           - networkx.Graph, subgraph of G containing only edges marked as UP in 'state'.
    """

    # init subgraph
    H = nx.Graph()
    H.add_nodes_from(G.nodes())

    # iterate over all edges of original graph
    for e in G.edges():
        # get left and right node adjacent to edge
        u, v = e
        # add edge to subgraph, if edge and adjacent nodes are UP
        if edge_state[e] == 1 and node_state[u] == 1 and node_state[v] == 1:
            H.add_edge(u,v)
    return H


def __get_lam_mu_from_graph(G):
            
    lam_edges, mu_edges = {}, {}
    lam_nodes, mu_nodes = {}, {}
    for e in G.edges(data=True):
        u, v, edata = e
        mtbf_h = edata.get('mtbf_h', 0) 
        lam = 0 if mtbf_h==0 else 1/mtbf_h        
        lam_edges.update({(u,v): lam})
        mttr_h = edata.get('mttr_h',0) 
        mu = 0 if mttr_h==0 else 1/mttr_h        
        mu_edges.update({(u,v): mu})
            
    for n in G.nodes(data=True):
        u, ndata = n        
        mtbf_h = ndata.get('mtbf_h', 0) 
        lam = 0 if mtbf_h==0 else 1/mtbf_h           
        lam_nodes.update({u: lam})
        mttr_h = ndata.get('mttr_h', 0) 
        mu = 0 if mttr_h==0 else 1/mttr_h                            
        mu_nodes.update({u: mu})
            
        
    return lam_edges, lam_nodes, mu_edges, mu_nodes

def __add_to_path_states(path_states, path_states_count, path_state_maxlen, state):    
    if len(path_states)<path_state_maxlen:
        path_states += [state]
        path_states_count += [1] 
    else:
        replace_index = path_states_count.index(min(path_states_count))
        path_states[replace_index] = state
        path_states_count[replace_index] += 1        
    return path_states, path_states_count



# ----------------------------------------------------------------------------------------------------------------------
# Monte-Carlo cycle for repairable systems
# ----------------------------------------------------------------------------------------------------------------------
def simulate_cycle_repairable(G, source, target, lam_edges, lam_nodes, mu_edges, mu_nodes, max_cycles=1, max_time=1e6):
    """
    monte-carlo simulation which simulates UP->DOWN - cycles for max_cycles deep (UP->DOWN->...->UP->DOWN).

    :INPUT:
        **G**           - networkx.Graph, system topology incl. failure and repair rates of nodes and edges.
        **source**      - Starting node
        **target**      - Target node
        **lam_edges**   - dict, failure rates for edges
        **lam_nodes**   - dict, failure rates for nodes
        **mu_edges**    - dict, repair rates for edges
        **mu_nodes**    - dict, repair rates for nodes
        **max_cycles**  - int, number of cycles to be simulated on the same (semi-fixed) network.
        **max_time**    - float, maximum simulation time, to avoid infinite loops.

    :OUTPUT:
        **mttf** - float, time until first system failure (MTTF sample)
        **mttr** - float, time until system is functional again after failure (MTTR sample)
    """


    # --- Phase 1: system starts UP and runs until disconnected ---
    # build list of states for edges and nodes
    edge_state = {e: 1 for e in G.edges()}  # all edges UP
    node_state = {n: 1 for n in G.nodes()}  # all nodes UP
    
    results = []
    
    path_states = [] # Lookup table for states with valid path
    path_states_count = [] # counter for states with valid path; used to limit size of path_states
    path_state_maxlen = 100     

    for _ in range(max_cycles):
        # --- Phase 1: System starts in some UP state depending on the previous cycle and runs until DOWN ---
        t_fail = 0.0
         
        while (edge_state in path_states) or nx.has_path(active_subgraph(G, edge_state, node_state), source, target):
            # TODO: check and add node state
            if edge_state not in path_states:
                path_states, path_states_count = __add_to_path_states(path_states, path_states_count, path_state_maxlen, edge_state.copy())    
            rates, transitions = [], []

            # build transition list for edges: failures for UP edges, repairs for DOWN edges
            for e, s in edge_state.items():
                if s == 1:
                    rates.append(lam_edges[e])
                    transitions.append(("edge", e, 0))
                else:
                    rates.append(mu_edges[e])
                    transitions.append(("edge", e, 1))

            # build transition list for nodes: failures for UP nodes, repairs for DOWN nodes
            for v, s in node_state.items():
                if s == 1:
                    rates.append(lam_nodes[v])
                    transitions.append(("node", v, 0))
                else:
                    rates.append(mu_nodes[v])
                    transitions.append(("node", v, 1))

            total = sum(rates)
            if total == 0: return None

            # sample time until next event ~ exp(total)
            dt = random.expovariate(total)
            t_fail += dt
            if t_fail > max_time: return None
            r = random.random() * total
            cum = 0.0

            # choose which event occurs next (weighted by rates)
            for rate, trans in zip(rates, transitions):
                cum += rate
                if r <= cum:
                    type, obj, newval = trans
                    if type == "edge":
                        edge_state[obj] = newval
                    elif type == "node":
                        node_state[obj] = newval
                    break

        # --- Phase 2: simulate until system is back UP. (Logic analagous to Phase 1, only with µ.) ---
        t_repair = 0.0
        while not nx.has_path(active_subgraph(G, edge_state, node_state), source, target):
            rates, transitions = [], []

            # build transition list: failures for UP edges, repairs for DOWN edges
            for e, s in edge_state.items():
                if s == 1:
                    rates.append(lam_edges[e])
                    transitions.append(("edge", e, 0))
                else:
                    rates.append(mu_edges[e])
                    transitions.append(("edge", e, 1))

            # build transition list: failures for UP nodes, repairs for DOWN nodes
            for v, s in node_state.items():
                if s == 1:
                    rates.append(lam_nodes[v])
                    transitions.append(("node", v, 0))
                else:
                    rates.append(mu_nodes[v])
                    transitions.append(("node", v, 1))

            total = sum(rates)
            if total == 0: return None

            # sample time until next event
            dt = random.expovariate(total)
            t_repair += dt
            if t_repair > max_time: return None

            # choose which event occurs next (weighted by rates)
            r = random.random() * total
            cum = 0.0

            # choose which event occurs next (weighted by rates)
            for rate, trans in zip(rates, transitions):
                cum += rate
                if r <= cum:
                    type, obj, newval = trans
                    if type == "edge":
                        edge_state[obj] = newval
                    elif type == "node":
                        node_state[obj] = newval
                    break
        
        results.append((t_fail, t_repair))

    if results is not []:
        mttf = statistics.mean([tf for tf, _ in results])
        mttr = statistics.mean([tr for _, tr in results])
        return mttf, mttr
    else:
        return None, None

# ----------------------------------------------------------------------------------------------------------------------
# Monte-Carlo cycle for non-repairable systems
# ----------------------------------------------------------------------------------------------------------------------
def simulate_time_to_failure_norepair(G, source, target, lam_edges, lam_nodes):
    """
    Simulate system lifetime for a non-repairable system (µ=0).
    :INPUT:
        **G** - networkx.Graph, system topology
        **source** - Starting node
        **target** - Target node
        **lam_dict** - dict, failure rates for edges

    :OUTPUT:
        **t** - float, time until first system failure (MTTF sample)
    """

    # init list of states for edges and nodes
    edge_state = {e: 1 for e in G.edges()}  # all edges UP
    node_state = {n: 1 for n in G.nodes()}  # all nodes UP

    t = 0.0
    while True:
        H = active_subgraph(G, edge_state, node_state)

        # stop if system is already disconnected (DOWN)
        if not nx.has_path(H, source, target):
            return t

        rates, transitions = [], []

        # build transition list for edges: failures for UP edges
        for e, s in edge_state.items():
            if s == 1:
                rates.append(lam_edges[e])
                transitions.append(("edge", e, 0))
        for v, s in node_state.items():
            if s == 1:
                rates.append(lam_nodes[v])
                transitions.append(("node", v, 0))

        total = sum(rates)
        if total == 0: return np.inf

        dt = random.expovariate(total)
        t += dt

        # choose failed edge / node
        r = random.random() * total
        cum = 0.0
        for rate, trans in zip(rates, transitions):
            cum += rate
            if r <= cum:
                type, obj, newval = trans
                if type == "edge":
                    edge_state[obj] = newval
                elif type == "node":
                    node_state[obj] = newval
                break


# ----------------------------------------------------------------------------------------------------------------------
# Monte-Carlo cycle for non-repairable systems
# ----------------------------------------------------------------------------------------------------------------------
def simulate_time_to_repair_nofailure(G, source, target, mu_dict):
    """
    Simulate system lifetime for a non-repairable system (µ=0).
    :INPUT:
        **G** - networkx.Graph, system topology
        **source** - Starting node
        **target** - Target node
        **lam_dict** - dict, failure rates for edges

    :OUTPUT:
        **t** - float, time until first system failure (MTTF sample)
    """
    alive_edges = list()
    dead_edges = list(G.edges())
    t = 0.0
    while True:
        H = nx.Graph()
        H.add_nodes_from(G.nodes())
        H.add_edges_from(alive_edges)

        # stop if system is already connected (UP)
        if nx.has_path(H, source, target):
            return t

        # next repair
        rates = [mu_dict[e] for e in dead_edges]
        total = sum(rates)
        dt = random.expovariate(total)
        t += dt

        # choose failed edge
        r = random.random() * total
        cum = 0.0
        for i, e in enumerate(dead_edges):
            cum += rates[i]
            if r <= cum:
                alive_edges.append(e)
                dead_edges.pop(i)
                break

# ----------------------------------------------------------------------------------------------------------------------
# run N Monte Carlo simulations and estimate reliability metrics from samples
# ----------------------------------------------------------------------------------------------------------------------
def estimate_mttf_mttr(G, source, target, N=1000, max_cycles=1):
    """
    Run N simulations and return reliability metrics

    :INPUT:
        **G** - networkx.Graph, system topology
        **source** - Starting node
        **target** - Target node
        **lam_dict** - dict, failure rates for edges
        **mu_dict** - dict, repair rates for edges
        **N** - int, number of simulations
        **max_cycles** - int, maximum number of cycles to simulate on the same network

    :OUTPUT:
        **MTTF** - float, mean time to failure
        **MTTR** - float, mean time to repair (None if µ=0)

    """

    # build dictionaries with rates of edges        
    lam_edges, lam_nodes, mu_edges, mu_nodes = __get_lam_mu_from_graph(G) 

    # non-repairable case
    if all(v==0 for v in mu_edges.values()) and all(v==0 for v in mu_nodes.values()):
        samples = [simulate_time_to_failure_norepair(G, source, target, lam_edges, lam_nodes) for _ in range(N)]
        return statistics.mean(samples), np.inf

    elif all(v==0 for v in lam_edges.values()) and all(v==0 for v in lam_nodes.values()):
        samples = [simulate_time_to_repair_nofailure(G, source, target, mu_edges) for _ in range(N)]
        return np.inf, statistics.mean(samples)

    # repairable case
    else:
        mttf_s, mttr_s = [], []
        for _ in range(N):
            res = simulate_cycle_repairable(G, source, target, lam_edges, lam_nodes, mu_edges, mu_nodes, max_cycles=max_cycles)
            if res is not None:
                tf, tr = res
                mttf_s.append(tf)
                mttr_s.append(tr)
        return statistics.mean(mttf_s), statistics.mean(mttr_s)
 