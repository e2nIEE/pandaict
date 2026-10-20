'''
# Copyright (c) 2016-2025 by Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.
Created on 13.09.2025

@author: fnuetz
'''

import networkx as nx
import random
import statistics

'''
Monte-Carlo Simulation for Network Reliability
==============================================

This program takes a NetworkX Graph, as well as failure rates λ (and optionally repair rates µ) for each edge of the 
graph as input and runs N Monte Carlo simulations to approximate the system reliability metrics MTTF, MTTR. 

Simulation logic: 
In case of non-repairable systems (µ=0), each edge can fail with a probability corresponding to its failure rate λ.
The system is considered functional as long as there exists at least one path (route) between source and target. Once
no such path exists anymore, the system is considered DOWN permanently. From the mean of the simulated lifetime samples 
the MTTF can be approximated.

In the repairable case (µ>0), an alternate Monte Carlo simulation is executed where in addition to the behavior 
described above the already failed edges have a probability, which correspond to their repair rate µ to be repaired and 
hence be UP again. The Simulation in this case is run for one whole UP and one whole DOWN cycle of the system to later
approximate the MTTF as well as the MTTR of the System.

Note:   For repairable systems the MTBF can be calculated from the returned metrics: MTBF = MTTF + MTTR
Note:   For networks with more than one route the MTTF explicitly depends on the MTTR. The reason for that is that 
        repairable systems generally tend to have higher MTTF, since failed components can be repaired before the system
        has failed.
Note:   Using failure rates µ << 1 (µ ~ 0) causes issues, which are grounded in the nature of the calculation: If the 
        repair rates are very small the system will stay DOWN for a long time which is why only a small sample size of 
        MTTF can be gathered in finite simulation time. This leads to large statistical fluctuations of the MTTF estimate. 
        Therefore in cases of very small µ it is recommended to consider the system as non-repairable and to set µ = 0.
Note:   Since this implementation allows to set the rates of each edge individually, mixing repair-rates equal to and
        bigger than zero can cause issues with convergence. This happens in cases in which single devices on a route can
        be fixed but not the whole route, since this leads to the system being down permanently but it is not catched by
        the simulation since the system is considered repairable.
Note:   I discovered that for repairable systems the MTTF is overestimated by the simulation. This happens because
        every Monte-Carlo 'Failure'-Cycle starts with a fully functional system (all edges up) while in reality, after 
        a system is repaired it might be in a semi-functional state, where there might be only one route between source 
        and target and as a result the system is more vulnerable then a fully functional system.
        The aim of v3 is to fix this issue. Until then the calculated MTTF for repairable systems should be viewed
        more like a Mean Time To First Failure (MTTFF).

Monte-Carlo Cycles:
The logic behind the individual Monte-Carlo Cycles is as follows: 
First the time until the next event is determined as follows: Each possible event (failure or repair) is modeled as an 
exponential random variable with its own rate (λ_i for failures, µ_i for repairs).
Since the system can only experience them one event at a time, we need the distribution of the minimum of all these
exponential distributions.
Mathematically, if the individual rates are λ_1, λ_2, ..., µ_i, ..., then the time to the next event follows an
exponential distribution with rate Parameter λ, given by the sum of all rates: 
T ~ exp(λ), λ = λ_1 + λ_2 + ... + λ_n + µ_1 + µ_2 + ... + µ_n 

Once we know that the next event happens after time T, we need to determine which (!) event will be the next.
The probability for event_i happening is given by P = µ_i / λ or λ_i / λ. Here this relation is realized by:
- drawing a random number from a uniform distribution r € [0, λ)
- partitioning the interval [0, λ) into subintervals of length λ_i or µ_i.
- selecting the event whose interval contains r
This ensures that events with higher rates are more likely, since the size of their corresponding intervals is 
proportional to their rate.

Now that we know what event happens next and when, we need to update the system state. This is done as follows:
- If the chosen event is failure, the corresponding edge is marked as failed and hence removed from the graph
- If it is a repair, the edge is restored, meaning added to the graph
- The global simulation clock is advanced by T

In the last step the system functionality is checked:
- If there still exists a path between source and target, the system is considered UP.
- If no such path exists, the system is DOWN.

Depending on the simulation mode, the cycle either ends after the system is down (µ = 0) or the cycle continues until a
sufficient number of failure/repair cycles have been simulated, allowing us to estimate MTTF, MTTR and hence MTBF.
'''

# ----------------------------------------------------------------------------------------------------------------------
# Helper: update the graph based on current edge states
# ----------------------------------------------------------------------------------------------------------------------
def active_subgraph(G, state):
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

    for _ in range(max_cycles):
        # --- Phase 1: System starts in some UP state depending on the previous cycle and runs until DOWN ---
        t_fail = 0.0
        while nx.has_path(active_subgraph(G, state), source, target):
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
            if t_fail > max_time: return None
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
        while not nx.has_path(active_subgraph(G, state), source, target):
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

    mttf = statistics.mean([tf for tf, _ in results])
    mttr = statistics.mean([tr for _, tr in results])
    return mttf, mttr

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
def estimate_mttf_mttr(G, source, target, lam_dict, mu_dict, N=1000, max_cycles=1):
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
    # non-repairable case
    if all(mu == 0 for mu in mu_dict.values()):
        samples = [simulate_time_to_failure_norepair(G, source, target, lam_dict) for _ in range(N)]
        return statistics.mean(samples), None

    # repairable case
    else:
        mttf_s, mttr_s = [], []
        for _ in range(N):
            res = simulate_cycle_repairable(G, source, target, lam_dict, mu_dict, max_cycles=max_cycles)
            if res is not None:
                tf, tr = res
                mttf_s.append(tf)
                mttr_s.append(tr)
        return statistics.mean(mttf_s), statistics.mean(mttr_s)


# ----------------------------------------------------------------------------------------------------------------------
# Implementation of some basic network topologies to run
# ----------------------------------------------------------------------------------------------------------------------
# 4Net_11:
def N4_11():
    G = nx.Graph()
    G.add_edges_from([
        ("S", "A"), ("A", "T"),
        ("S", "B"), ("B", "T")
    ])
    lam = {
        ("S", "A"): 1,
        ("A", "T"): 1,
        ("S", "B"): 1,
        ("T", "B"): 1
    }
    mu = {
        ("S", "A"): 1,
        ("A", "T"): 1,
        ("S", "B"): 1,
        ("T", "B"): 1
    }
    return G, lam, mu

# 4Net_21
def N4_21():
    G = nx.Graph()
    G.add_edges_from([
        ("S", "A"), ("A", "T"),
        ("S", "B"), ("B", "T"),
        ("A", "B")
    ])
    lam = {
        ("S", "A"): 1,
        ("A", "T"): 1,
        ("S", "B"): 1,
        ("T", "B"): 1,
        ("A", "B"): 1
    }
    mu = {
        ("S", "A"): 1e-1,
        ("A", "T"): 1e-1,
        ("S", "B"): 0,
        ("T", "B"): 0,
        ("A", "B"): 0
    }
    return G, lam, mu

# 4Net_22
def N4_22():
    G = nx.Graph()
    G.add_edges_from([
        ("S", "A"), ("A", "T"),
        ("S", "B"), ("B", "T"),
        ("S", "T")
    ])
    lam = {
        ("S", "A"): 1,
        ("A", "T"): 1,
        ("S", "B"): 1,
        ("T", "B"): 1,
        ("S", "T"): 1
    }
    mu = {
        ("S", "A"): 1e-1,
        ("A", "T"): 1e-1,
        ("S", "B"): 1e-1,
        ("T", "B"): 1e-1,
        ("S", "T"): 1e-1
    }
    return G, lam, mu

# 4Net_31
def N4_31():
    G = nx.Graph()
    G.add_edges_from([
        ("S", "A"), ("A", "T"),
        ("S", "B"), ("B", "T"),
        ("S", "T"), ("A", "B")
    ])
    lam = {
        ("S", "A"): 1,
        ("A", "T"): 1,
        ("S", "B"): 1,
        ("T", "B"): 1,
        ("S", "T"): 1,
        ("A", "B"): 1
    }
    mu = {
        ("S", "A"): 1e-1,
        ("A", "T"): 1e-1,
        ("S", "B"): 1e-1,
        ("T", "B"): 1e-1,
        ("S", "T"): 1e-1,
        ("A", "B"): 1e-1
    }
    return G, lam, mu

# 6N-seriell
def N6_seriell():
    G = nx.Graph()
    G.add_edges_from([
        ("S", "1"), ("1", "2"), ("2", "3"), ("3", "4"), ("4", "5"), ("5", "T")
    ])
    lam = {
        ("S", "1"): 1.0,
        ("1", "2"): 1.0,
        ("2", "3"): 1.0,
        ("3", "4"): 1.0,
        ("4", "5"): 1.0,
        ("5", "T"): 1.0
    }
    mu = {
        ("S", "1"): 1.0,
        ("1", "2"): 1.0,
        ("2", "3"): 1.0,
        ("3", "4"): 1.0,
        ("4", "5"): 1.0,
        ("5", "T"): 1.0
    }
    return G, lam, mu

# pandapower-pandaICT-connector
def pp_pi_connector():
    G = nx.Graph()
    G.add_edges_from([
        ("CC", "1"), ("1", "2"),
        ("2", "conv1"), ("conv1", "pc1"),
        ("2", "conv2"), ("conv2", "pc2"),
        ("2", "conv3"), ("conv3", "sc"),
        ("2", "pq1"),
        ("2", "pq2")
    ])
    lam = {
        ("CC", "1"):    1.0,
        ("1", "2"):     1.0,
        ("2", "conv1"): 1.0,
        ("conv1", "pc1"): 1.0,
        ("2", "conv2"): 1.0,
        ("conv2", "pc2"): 1.0,
        ("2", "conv3"): 1.0,
        ("conv3", "sc"): 1.0,
        ("2", "pq1"):   1.0,
        ("2", "pq2"):   1.0
    }
    mu = {
        ("CC", "1"): 1.0,
        ("1", "2"): 1.0,
        ("2", "conv1"): 1.0,
        ("conv1", "pc1"): 1.0,
        ("2", "conv2"): 1.0,
        ("conv2", "pc2"): 1.0,
        ("2", "conv3"): 1.0,
        ("conv3", "sc"): 1.0,
        ("2", "pq1"): 1.0,
        ("2", "pq2"): 1.0
    }
    return G, lam, mu

# ----------------------------------------------------------------------------------------------------------------------
# EXAMPLE USAGE
# ----------------------------------------------------------------------------------------------------------------------

# declare source and target nodes
source, target = "CC", "pc2"

# choose network
# functions return Graph G, dict of failure rates lam={1/MTTF_i} and dict of repair rates mu={1/MTTR_i} for each link.
G, lam, mu = pp_pi_connector()

# repairable case
if any(µ > 0 for µ in mu.values()):
    mttf, mttr = estimate_mttf_mttr(G, source, target, lam, mu, N=500, max_cycles=200)
    print('\n------- REPARABLE -------')
    print("MTTF:", round(mttf, 3))
    print("MTTR:", round(mttr, 3))
    print("MTBF:", round(mttf+mttr, 3))

# non-repairable case (μ = 0)
else:
    mu0 = {e: 0.0 for e in G.edges()}
    mttf_nr, _ = estimate_mttf_mttr(G, source, target, lam, mu0, N=100000)
    print("\n------ NON-REPARABLE -----")
    print("MTTF:", round(mttf_nr, 3))

