'''
Created on 22.12.2025
@author: fnuetz

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

# main API
import numpy as np
from pandaict.pilogger import pilogger
from pandaict.reliability.reliability_utils import _get_lam_mu_from_graph

# import python fallback
from pandaict.reliability.monte_carlo_python_fallback import (
        _run_python,
    )

from pandaict.reliability.monte_carlo_helpers import (
        _check_initial_connectivity,
        _normalize_connection_pairs,
        _graph_to_numba_arrays,
        _filter_results,
        _print_criticality,
        _calc_criticalities,
        _save_criticality_excel,
        _rates_to_arrays,
        _count_events,
        _expected_fractions,
    )

# try importing wrappers for numba version
try:
    from pandaict.reliability.monte_carlo_numba_wrappers import (
        _run_numba
    )
    NUMBA_AVAILABLE = True

except ImportError:
    NUMBA_AVAILABLE = False
    pilogger.warning("Warning: Numba not available. Using Python-only version.")


# ----------------------------------------------------------------------------------------------------------------------
# Critical Component Analysis
# ----------------------------------------------------------------------------------------------------------------------
def analyze_critical_components(all_critical, G, sources, targets,
                                lam_edges, lam_nodes,
                                mu_edges, mu_nodes,
                                top_n=-1, verbose=True,
                                rate_adjustment=True,
                                save_excel=False, excel_path=None,
                                edge_labels=None, node_labels=None
                                ):
    """

    Analyze which components are disproportionately critical by calculating the expected
    :INPUT:

        **all_critical**    - array of all critical components returned by monte_carlo

        **n_edges**         - int, number of edges on graph

        **n_nodes**         - int, number of nodes on graph

        **edge_list**       - list of all edges

        **node_list**       - list of all nodes

        **lam_edges_arr**   - array of failure rates (edges)

        **lam_nodes_arr**   - array of failure rates (nodes)

        **mu_edges_arr**    - array of repair rates (edges)

        **mu_nodes_arr**    - array of repair rates (nodes)

        **top_n**           - int, number of most critical components to be displayed

        **verbose**         - bool, prints component criticalities to console

        **rate_adjustment** - bool, choose whether to adjust the counts by their rates.
                              This determines whether the network is analyzed for bare topological
                              criticalities (True) or a wholistic analysis of critical components
                              is performed, which explicitly depends on the rates of the components (False).

        **save_excel**      - bool, save calculated component criticalities in an excel file for further analysis.
        **excel_path**      - string, saving path for the excel spreadsheet. (default=current directory)

    :OUTPUT:
        dict with edge_criticality, node_criticality, counts, plots, etc.

    """
    if top_n == 0:
        top_n = -1

    # get graph in csr-array format
    conv = _graph_to_numba_arrays(G, sources, targets)

    edge_list = conv['edge_list']
    node_list = conv['node_list']
    n_edges = len(edge_list)
    n_nodes = len(node_list)
    n_events = n_edges + n_nodes

    lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr = \
        _rates_to_arrays(edge_list, node_list,
                         lam_edges, lam_nodes, mu_edges, mu_nodes)
    
    failure_counts, repair_counts, total_failure, total_repair = \
        _count_events(all_critical, n_events)

    if failure_counts is None:
        pilogger.info("No critical components tracked!")
        return None

    total_observed = total_failure + total_repair

    lam_all = np.concatenate([lam_edges_arr, lam_nodes_arr])
    mu_all = np.concatenate([mu_edges_arr, mu_nodes_arr])

    # Failure-Baseline & Repair-Baseline
    failure_fractions = _expected_fractions(lam_all, n_events)
    repair_fractions = _expected_fractions(mu_all, n_events)

    # calculate criticality scores
    failure_crit = _calc_criticalities(
        n_events, total_failure, failure_fractions,
        failure_counts, rate_adjustment)

    repair_crit = _calc_criticalities(
        n_events, total_repair, repair_fractions,
        repair_counts, rate_adjustment)

    # split in edges and nodes
    edge_fail_crit = failure_crit[:n_edges]
    node_fail_crit = failure_crit[n_edges:]
    edge_rep_crit = repair_crit[:n_edges]
    node_rep_crit = repair_crit[n_edges:]

    # sort values
    top_edge_fail_idx = np.argsort(edge_fail_crit)[::-1]
    top_node_fail_idx = np.argsort(node_fail_crit)[::-1]
    top_edge_rep_idx = np.argsort(edge_rep_crit)[::-1]
    top_node_rep_idx = np.argsort(node_rep_crit)[::-1]

    if verbose:
        _print_criticality(total_observed, total_failure, total_repair, top_n,
                           top_edge_fail_idx, top_edge_rep_idx, edge_list,
                           edge_fail_crit, edge_rep_crit, n_edges,
                           top_node_fail_idx, top_node_rep_idx, node_list,
                           node_fail_crit, node_rep_crit, n_nodes,
                           failure_counts, repair_counts,
                           edge_labels, node_labels)

    if save_excel:
        _save_criticality_excel(
            total_observed, failure_crit, top_n,
            top_edge_fail_idx, edge_list, edge_fail_crit, n_edges,
            top_node_fail_idx, node_list, node_fail_crit, failure_counts,
            excel_path,
            edge_labels, node_labels)

    return {
        'edge_criticality': edge_fail_crit,
        'node_criticality': node_fail_crit,
        'edge_repair_criticality': edge_rep_crit,
        'node_repair_criticality': node_rep_crit,
        'failure_counts': failure_counts,
        'repair_counts': repair_counts,
        'total_observed': total_observed,
        'total_failure': total_failure,
        'total_repair': total_repair,
    }


def empirical_reliability(T, samples):
    """
    Builds empirical reliability function R and returns its value at timepoint T: R(T)=P(t>T).

    :INPUT:
        **T**       - float, timepoint at which the reliability will be evaluated.

        **samples** - np.ndarray, mttf samples

    :OUTPUT:
        **R**       - float, reliability function evaluated at timepoint T: R(T)=P(t>=T).
    """

    n = len(samples)

    if n==0:
        return 0.0

    n_failure = np.sum(samples <= T)
    n_survivor = n - n_failure

    reliability = n_survivor / n

    return reliability


# ----------------------------------------------------------------------------------------------------------------------
# Main API: run N Monte Carlo simulations and estimate reliability metrics from samples
# ----------------------------------------------------------------------------------------------------------------------
def estimate_mttf_mttr(G, sources, targets, min_connected=-1,
                       N=1000, depth=200,
                       max_time=np.inf, max_events=-1,
                       analyze_crit=False, laziness=0,
                       use_numba=True, parallel=True):
    """
    Run N Monte Carlo simulations and estimate MTTF/MTTR.

    :INPUT:
        **G**                   - NetworkX graph with 'mtbf_h' and 'mttr_h' attributes on nodes and edges.

        **sources**             - Source node(s)

        **targets**             - Target node(s)

        **min_connected**       - int, minimum number of connected source-target-pairs required
            - min_connected=1:  At least 1 pair (any)
            - min_connected=k:  At least k pairs (k-out-of-n)
            - min_connected=-1: All pairs (all) (default)

        **N**:                  - Number of simulation runs. It is recommended to not use more than 1e9, since beyond
                                  that most systems will run into memory issues. Samples are stored as np.float64,
                                  allocating 11 bits exponent and 52 bits mantissa resulting in.
                                  1e9 samples result in ~8GB of RAM usage.

        **depth**               - Number of UP/DOWN cycles per simulation run (only repairable).
                                  Adjusts for the natural bias towards larger reliabilities when starting each new cycle
                                  with a fully functional network. Depth hands over a semi-fixed network into the next cycle.
                                  ~200 gives reasonable values.

        **max_time**            - float, parameter to optimize sample collection for empirical reliability function type
                                  calculations.

        **max_events**          - int, control maximum number of events to avoid infinite loops for super-robust networks.

        **analyze_crit**        - Boolean, choose whether network should be analyzed for critical components.

        **laziness**            - float in [0,1), parameter which allows to sacrifice some accuracy for performance.
                                  Only checks the connectivity of the network if laziness*(V+E) events took place (only numba).

        **use_numba**           - Boolean, use Numba-optimized version if available (default: True)

        **parallel**            - Boolean, enable parallelization (default: True)

    :OUTPUT:
        {
        **mttf**                - float, mean time to failure

        **mttr**                - float, mean time to repair (np.inf if non-repairable)

        **mttf_samples**        - np.ndarray, mttf samples

        **mttr_samples**        - np.ndarray, mttr samples
        }
    """
    
    # TODO: Remove max_events, laziness for release. remove TOL and return_samples until implemented.
    # TODO: Check if N and depth can be collapsed to one argument => No!
    
    sources, targets = _normalize_connection_pairs(sources, targets)

    # Catch if G is not connected at start.
    is_connected, error_msg = _check_initial_connectivity(G, sources, targets, min_connected)

    if not is_connected:
        pilogger.warning(f'Initial connectivity check failed: {error_msg}')
        pilogger.warning('Please fix topology!')
        return {'mttf': None, 'mttr': None, 'mttf_samples': None, 'mttr_samples': None}

    # Extract rates from graph
    lam_edges, lam_nodes, mu_edges, mu_nodes = _get_lam_mu_from_graph(G)

    # Check for non-repairable case
    is_nonrepairable = (all(mu == 0 for mu in mu_edges.values()) and all(mu == 0 for mu in mu_nodes.values()))
    is_repairable = not is_nonrepairable

    all_critical = None
    edge_criticality = None
    node_criticality = None

    # Check if all rates are zero and warn
    is_nofailure = (all(lam == 0 for lam in lam_edges.values()) and all(lam == 0 for lam in lam_nodes.values()))

    # Check for no-failure case
    if is_nofailure:
        pilogger.warning('All failure rates are zero. Please adjust!')
        return {'mttf':np.inf, 'mttr':0.0, 'mttf_samples':None, 'mttr_samples':None}

    if use_numba and NUMBA_AVAILABLE:
        all_results, all_critical = _run_numba(G, sources, targets, min_connected, is_repairable,
                                               lam_edges, lam_nodes, mu_edges, mu_nodes,
                                               N, depth,
                                               max_time, max_events,
                                               analyze_crit, laziness,
                                               parallel)

    else:
        # Python fallback
        pilogger.warning("Warning! Using deprecated python fallback. Consider using numba to get access to maintained version.")
        pilogger.warning(f"Using Python fallback ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

        sources = sources[0]
        targets = targets[0]

        all_results = _run_python(G, sources, targets, is_repairable, lam_edges, lam_nodes, mu_edges, mu_nodes, N, depth)

    # filter results
    valid_results = _filter_results(all_results, is_repairable, max_time)

    # unpack results
    mttf_clean_samples = valid_results['mttf_samples']
    mttr_clean_samples = valid_results['mttr_samples']

    # calc mean values
    mttf = 0.0 if mttf_clean_samples is None else float(np.mean(mttf_clean_samples))
    mttr = np.inf if mttr_clean_samples is None else float(np.mean(mttr_clean_samples))

    
    if is_repairable:
        mttf_samples = all_results[:, 0]
        mttr_samples = all_results[:, 1]

    else:
        mttf_samples = all_results
        mttr_samples = None

    return {'mttf': mttf,
            'mttr': mttr,
            'mttf_samples': mttf_samples,
            'mttr_samples': mttr_samples,
            'edge_criticality': edge_criticality,
            'node_criticality': node_criticality,
            'all_critical': all_critical,}






