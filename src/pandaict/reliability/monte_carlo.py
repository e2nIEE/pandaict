'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 20.11.2025

@author: fnuetz, jringelstein
'''


from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.reliability.reliability_utils import __get_next_hop, __check_calc_route, __check_lup_prob_sum_lt_one
from pandaict.utils.enums import RoutingType, SortType
from pandaict.pilogger import pilogger

import math
import networkx as nx
import random
import statistics  
   
#----------------------------------------------------------------------------------------------------------------------
# Helper: update the graph based on current edge states
# ----------------------------------------------------------------------------------------------------------------------
def __active_subgraph(G, state):
    """
    Return subgraph of G containing only edges marked as UP in 'state'.

    :INPUT:
        **G** - networkx.Graph, original graph
        **state** - dict, edge status {edge: 0/1}, with 1 = UP, 0 = DOWN.

    :OUTPUT:
        **H** - networkx.Graph, subgraph of G containing only edges marked as UP in 'state'.
    """

    H = nx.Graph()
    H.add_nodes_from(G.nodes())
    for edge, status in state.items():
        if status == 1:
            H.add_edge(*edge)
    return H


def __get_lam_mu_from_graph(G):
    lam = {}
    mu = {}
    for e in G.edges():
        edata = G.get_edge_data(e[0], e[1])[0]
        mtbf_h = edata.get('mtbf_h', 0) 
        if mtbf_h!=0:
            lam.update({(e[0], e[1]): 1/mtbf_h})
        mttr_h = edata.get('mttr_h',0) 
        if mttr_h!=0:
            mu.update({(e[0], e[1]): 1/mttr_h})
        
    return lam, mu 

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
def simulate_cycle_repairable(G, source, target, lam_dict, mu_dict, max_cycles=1, max_time=1e6):
    """
    monte-carlo simulation which simulates UP->DOWN - cycles for max_cycles deep (UP->DOWN->...->UP->DOWN).

    :INPUT:
        **G** - networkx.Graph, system topology
        **source** - Starting node
        **target** - Target node
        **lam_dict** - dict, failure rates for edges
        **mu_dict** - dict, repair rates for edges
        **max_cycles** - int, number of cycles to be simulated on the same (half-fixed) network.
        **max_time** - float, maximum simulation time, to avoid infinite loops.

    :OUTPUT:
        **mttf** - float, time until first system failure (MTTF sample)
        **mttr** - float, time until system is functional again after failure (MTTR sample)
    """

    # --- Phase 1: system starts UP and runs until disconnected ---
    state = {e: 1 for e in G.edges()}  # alle Kanten UP
    t = 0.0
    results = []

    path_states = [] # Lookup table for states with valid path
    path_states_count = [] # counter for states with valid path; used to limit size of path_states
    path_state_maxlen = 100 
    
    for _ in range(max_cycles):
        # --- Phase 1: System starts in some UP state depending on the previous cycle and runs until DOWN ---
        t_fail = 0.0
        while (state in path_states) or (nx.has_path(__active_subgraph(G, state), source, target)):
            if state not in path_states:
                path_states, path_states_count = __add_to_path_states(path_states, path_states_count, path_state_maxlen, state.copy())                     
            rates, transitions = [], []

            # build transition list: failures for UP edges, repairs for DOWN edges
            for e, s in state.items():
                if s == 1:
                    rates.append(lam_dict[e])
                    transitions.append((e, 0))
                else:
                    rates.append(mu_dict[e])
                    transitions.append((e, 1))

            total = sum(rates)
            if total == 0: return None

            # sample time until next event ~ exp(total)
            dt = random.expovariate(total)
            t_fail += dt
            if t_fail > max_time: 
                return None
            r = random.random() * total
            cum = 0.0

            # choose which event occurs next (weighted by rates)
            for rate, trans in zip(rates, transitions):
                cum += rate
                if r <= cum:
                    edge, newval = trans
                    state[edge] = newval
                    break

        # --- Phase 2: simulate until system is back UP. (Logic analagous to Phase 1, only with µ.) ---
        t_repair = 0.0
        while not nx.has_path(__active_subgraph(G, state), source, target):
            rates, transitions = [], []

            # build transition list: failures for UP edges, repairs for DOWN edges
            for e, s in state.items():
                if s == 1:
                    rates.append(lam_dict[e])
                    transitions.append((e, 0))
                else:
                    rates.append(mu_dict[e])
                    transitions.append((e, 1))

            total = sum(rates)
            if total == 0: return None

            # sample time until next event
            dt = random.expovariate(total)
            t_repair += dt
            if t_repair > max_time: return None

            # choose which event occurs next (weighted by rates)
            r = random.random() * total
            cum = 0.0
            for rate, trans in zip(rates, transitions):
                cum += rate
                if r <= cum:
                    edge, newval = trans
                    state[edge] = newval
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
def simulate_time_to_failure_norepair(G, source, target, lam_dict):
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
    alive_edges = list(G.edges())
    t = 0.0
    while True:
        H = nx.Graph()
        H.add_nodes_from(G.nodes())
        H.add_edges_from(alive_edges)

        # stop if system is already disconnected (DOWN)
        if not nx.has_path(H, source, target):
            return t
        if not alive_edges:
            return t

        # determine when next failure happens
        rates = [lam_dict[e] for e in alive_edges]
        total = sum(rates)
        dt = random.expovariate(total)
        t += dt

        # choose edge to fail
        r = random.random() * total
        cum = 0.0
        for i, e in enumerate(alive_edges):
            cum += rates[i]
            if r <= cum:
                alive_edges.pop(i)
                break

# ----------------------------------------------------------------------------------------------------------------------
# run N Monte Carlo simulations and estimate reliability metrics from samples
# ----------------------------------------------------------------------------------------------------------------------
def estimate_mttf_mttr(G, source, target, N=1000, max_cycles=1):
    """
    Run N simulations and return reliability metrics

    :INPUT:
        **G** - networkx.Graph, system topology for connection, edges and 
        **conn** - pandaict connection  
        **downstream** - If True, conn['from_app]' is used as sender and conn['to_app]' as receiver. If False, they are swapped.                        
        **N** - int, number of simulations
        **max_cycles** - int, maximum number of cycles to simulate on the same network

    :OUTPUT:
        **(MTTF, MTTR)** - tuple of float, mean time to failure and mean time to repair (None if mu=0)        

    """
    
    lam_dict, mu_dict = __get_lam_mu_from_graph(G)                
    
    # non-repairable case
    if all(mu == 0 for mu in mu_dict.values()):
        samples = [simulate_time_to_failure_norepair(G, source, target, lam_dict) for _ in range(N)]
        return statistics.mean(samples), None

    # repairable case
    else:
        mttf_s, mttr_s = [], []
        for n in range(N):
            print(str(n))
            res = simulate_cycle_repairable(G, source, target, lam_dict, mu_dict, max_cycles=max_cycles)
            if res is not None:
                tf, tr = res
                mttf_s.append(tf)
                mttr_s.append(tr)        
                        
        return statistics.mean(mttf_s) if len(mttf_s) else None, statistics.mean(mttr_s) if len(mttr_s) else None

 