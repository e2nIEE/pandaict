'''
Created on 22.12.2025
@author: fnuetz

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

import numpy as np
from numba import njit, prange
from pandaict.pilogger import pilogger
from pandaict.reliability.monte_carlo_numba_core import (
    _build_rates_and_bit,
    simulate_numba_core,
    simulate_numba_core_norepair
)
from pandaict.reliability.monte_carlo_helpers import (
    _graph_to_numba_arrays
)

# ------------------------------------------------------------------------------------------------------------------
# Wrappers for parallel and serial code execution
# ------------------------------------------------------------------------------------------------------------------
@njit(parallel=True)
def _run_parallel(n_sims, depth, TOL,
                  n_edges, n_nodes,
	              adj_offsets, adj_nodes, adj_edges,
                  lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr,
                  source_idx, target_idx, min_connected,
                  max_events, max_time,
	              return_samples, analyze_crit, laziness):
    """
    Wrapper for running n_sims repairable simulations in parallel.
    Facilitates all N CPU-Cores to each run n_sims simulations
    Speedup: ~Nx with N Cores.
    """
    # TODO: implement convergence criteria (TOL)
    # TODO: use return samples to improve memory efficiency

    all_results = np.empty((n_sims, 2), dtype=np.float64)

    # Build event list
    n_events = n_edges + n_nodes

    # prebuild fenwick tree
    bit_template = _build_rates_and_bit(n_edges, n_nodes,
                                        lam_edges_arr, lam_nodes_arr)

    # threshold to check connectivity
    event_threshold = int(laziness * n_events)

    # calc max events per simulation to store critical components
    max_crit_per_sim = 2 * (event_threshold + 1) * depth

    if analyze_crit:
        # preallocate array for critical components
        all_critical = np.full((n_sims, max_crit_per_sim), -1, dtype=np.int32)
    else:
        all_critical = np.empty((0, 0), dtype=np.int32)

    # core parallelisation routine
    for sim_idx in prange(n_sims):
        bit = bit_template.copy()

        results, crit_comp = simulate_numba_core(
            depth,
            n_edges, n_nodes,
            adj_offsets, adj_nodes, adj_edges,
            lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr, bit,
            source_idx, target_idx, min_connected,
            max_events, max_time,
            analyze_crit, laziness
        )

        if results.shape[0] > 0:
            # TODO: maybe adjust such that samples instead of mean is stored in all_results? okay for now.
            all_results[sim_idx, 0] = float(np.mean(results[:, 0]))
            all_results[sim_idx, 1] = float(np.mean(results[:, 1]))

            if analyze_crit:
                n_crit = min(crit_comp.shape[0], max_crit_per_sim)
                all_critical[sim_idx, :n_crit] = crit_comp[:n_crit]
        else:
            # mark as invalid
            all_results[sim_idx, :] = np.nan

    return all_results, all_critical


@njit(parallel=True)
def _run_parallel_norepair(n_sims, TOL,
                           n_edges, n_nodes,
                           adj_offsets, adj_nodes, adj_edges,
                           lam_edges_arr, lam_nodes_arr,
                           source_idx, target_idx, min_connected,
	                       max_events, max_time,
	                       return_samples, analyze_crit, laziness):
    """
    Wrapper for running n_sims non-repairable simulations in parallel.
    Facilitates all N CPU-Cores to each run n_sims/N simulations
    Speedup: ~Nx with N Cores.
    """
    # TODO: implement analyze_crit
    # TODO: use return samples to improve memory efficiency
    # TODO: implement convergence criteria (TOL)

    all_results = np.empty(n_sims, dtype=np.float64)
    n_events = n_edges + n_nodes

    bit_template = _build_rates_and_bit(n_edges, n_nodes,
                                        lam_edges_arr, lam_nodes_arr)

    # Critical components storage
    event_threshold = int(laziness * n_events)

    max_crit_per_sim = event_threshold + 1

    if analyze_crit:
        all_critical = np.full((n_sims, max_crit_per_sim), -1, dtype=np.int32)
    else:
        all_critical = np.empty((0, 0), dtype=np.int32)

    for sim_idx in prange(n_sims):
        bit = bit_template.copy()

        result, crit_comp = simulate_numba_core_norepair(
            n_edges, n_nodes,
            adj_offsets, adj_nodes, adj_edges,
            lam_edges_arr, lam_nodes_arr, bit,
            source_idx, target_idx, min_connected,
            max_events, max_time,
            analyze_crit, laziness
        )
        all_results[sim_idx] = result

        if analyze_crit:
            n_crit = min(crit_comp.shape[0], max_crit_per_sim)
            all_critical[sim_idx, :n_crit] = crit_comp[:n_crit]

    return all_results, all_critical


@njit
def _run_serial(n_sims, depth, TOL,
	            n_edges, n_nodes,
	            adj_offsets, adj_nodes, adj_edges,
                lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr,
                source_idx, target_idx, min_connected,
                max_events, max_time,
	            return_samples, analyze_crit, laziness):
    """
    Wrapper to run n_sims repairable simulations serially.
    Same structure as parallel, but with range instead of prange.
    """
    # TODO: implement convergence criteria (TOL)
    # TODO: use return samples to improve memory efficiency

    all_results = np.empty((n_sims, 2), dtype=np.float64)
    n_events = n_edges + n_nodes

    # Prebuild Fenwick Tree
    bit_template = _build_rates_and_bit(n_edges, n_nodes,
                                        lam_edges_arr, lam_nodes_arr)

    # Critical components storage
    event_threshold = int(laziness * n_events)

    max_crit_per_sim = 2 * (event_threshold + 1) * depth

    if analyze_crit:
        all_critical = np.full((n_sims, max_crit_per_sim), -1, dtype=np.int32)
    else:
        all_critical = np.empty((0, 0), dtype=np.int32)

    # Serial loop
    for sim_idx in range(n_sims):
        bit = bit_template.copy()

        results, crit_comp = simulate_numba_core(
            depth,
            n_edges, n_nodes,
            adj_offsets, adj_nodes, adj_edges,
            lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr, bit,
            source_idx, target_idx, min_connected,
            max_events, max_time,
            analyze_crit, laziness
        )

        if results.shape[0] > 0:
            # TODO: maybe adjust such that samples instead of mean is stored in all_results? okay for now.
            all_results[sim_idx, 0] = np.mean(results[:, 0])
            all_results[sim_idx, 1] = np.mean(results[:, 1])

            if analyze_crit:
                n_crit = min(crit_comp.shape[0], max_crit_per_sim)
                all_critical[sim_idx, :n_crit] = crit_comp[:n_crit]
        else:
            all_results[sim_idx, :] = np.nan

    return all_results, all_critical


@njit
def _run_serial_norepair(n_sims, TOL,
                         n_edges, n_nodes,
                         adj_offsets, adj_nodes, adj_edges,
                         lam_edges_arr, lam_nodes_arr,
                         source_idx, target_idx, min_connected,
	                     max_events, max_time,
	                     return_samples, analyze_crit, laziness):
    """Wrapper for running n_sims non-repairable simulations serially."""

    # TODO: implement convergence criteria (TOL)
    # TODO: use return samples to improve memory efficiency
    # TODO: implement analyze_crit


    all_results = np.empty(n_sims, dtype=np.float64)
    n_events = n_edges + n_nodes

    bit_template = _build_rates_and_bit(n_edges, n_nodes,
                                        lam_edges_arr, lam_nodes_arr)

    # Critical components storage
    event_threshold = int(laziness * n_events)

    max_crit_per_sim = event_threshold + 1

    if analyze_crit:
        all_critical = np.full((n_sims, max_crit_per_sim), -1, dtype=np.int32)
    else:
        all_critical = np.empty((0, 0), dtype=np.int32)

    for sim_idx in range(n_sims):
        bit = bit_template.copy()

        result, crit_comp = simulate_numba_core_norepair(
            n_edges, n_nodes,
            adj_offsets, adj_nodes, adj_edges,
            lam_edges_arr, lam_nodes_arr, bit,
            source_idx, target_idx, min_connected,
            max_events, max_time,
            analyze_crit, laziness
        )
        all_results[sim_idx] = result

        if analyze_crit:
            n_crit = min(crit_comp.shape[0], max_crit_per_sim)
            all_critical[sim_idx, :n_crit] = crit_comp[:n_crit]

    return all_results, all_critical


def _run_numba(G, sources, targets, min_connected, is_repairable,		    # Topology and connectivity
               lam_edges, lam_nodes, mu_edges, mu_nodes,
               N, depth, TOL,										        # number of samples
               max_time, max_events,								        # early stoppage
               return_samples, analyze_crit, laziness,		                # calculation method
               parallel):

    # Convert graph to arrays
    conv = _graph_to_numba_arrays(G, sources, targets)

    # get edge and node arrays
    lam_edges_arr = np.array([lam_edges[e] for e in conv['edge_list']], dtype=np.float64)
    lam_nodes_arr = np.array([lam_nodes[n] for n in conv['node_list']], dtype=np.float64)

    if not is_repairable:
        # non-repairable case
        if parallel:
            pilogger.info(f"Running {N} simulations in parallel...")
            all_results, all_critical = _run_parallel_norepair(
                N, TOL,
                conv['n_edges'], conv['n_nodes'],
                conv['adj_offsets'], conv['adj_nodes'], conv['adj_edges'],
                lam_edges_arr, lam_nodes_arr,
                conv['source_idx'], conv['target_idx'], min_connected,
                max_events, max_time,
                return_samples, analyze_crit, laziness
            )
        else:
            all_results, all_critical = _run_serial_norepair(
                N, TOL,
                conv['n_edges'], conv['n_nodes'],
                conv['adj_offsets'], conv['adj_nodes'], conv['adj_edges'],
                lam_edges_arr, lam_nodes_arr,
                conv['source_idx'], conv['target_idx'], min_connected,
                max_events, max_time,
                return_samples, analyze_crit, laziness
            )

    else:
        # Repairable case
        mu_edges_arr = np.array([mu_edges[e] for e in conv['edge_list']], dtype=np.float64)
        mu_nodes_arr = np.array([mu_nodes[n] for n in conv['node_list']], dtype=np.float64)

        pilogger.info(f"Running {N * depth} ({N} x {depth}) simulations {'in parallel' if parallel else ''}...")

        if parallel:
            all_results, all_critical = _run_parallel(
                N, depth, TOL,
                conv['n_edges'], conv['n_nodes'],
                conv['adj_offsets'], conv['adj_nodes'], conv['adj_edges'],
                lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr,
                conv['source_idx'], conv['target_idx'], min_connected,
                max_events, max_time,
                return_samples, analyze_crit, laziness
            )
        else:
            all_results, all_critical = _run_serial(
                N, depth, TOL,
                conv['n_edges'], conv['n_nodes'],
                conv['adj_offsets'], conv['adj_nodes'], conv['adj_edges'],
                lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr,
                conv['source_idx'], conv['target_idx'], min_connected,
                max_events, max_time,
                return_samples, analyze_crit, laziness
            )

    return all_results, all_critical

