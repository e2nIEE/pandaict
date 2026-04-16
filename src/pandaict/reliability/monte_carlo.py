'''
Created on 22.12.2025
@author: fnuetz
'''

# main API
import numpy as np
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
        _critical_bar_plot,
        _print_criticality,
        _calc_criticalities,
        _save_criticality_excel
    )

# try importing wrappers for numba version
try:
    from pandaict.reliability.monte_carlo_numba_wrappers import (
        _run_numba,
        _run_parallel,
        _run_parallel_norepair,
        _run_serial,
        _run_serial_norepair
    )
    NUMBA_AVAILABLE = True

except ImportError:
    NUMBA_AVAILABLE = False
    print("Warning: Numba not available. Using Python-only version.")


# ----------------------------------------------------------------------------------------------------------------------
# Critical Component Analysis
# ----------------------------------------------------------------------------------------------------------------------
def analyze_critical_components(all_critical, G, sources, targets,
                                lam_edges, lam_nodes,
                                mu_edges, mu_nodes,
                                top_n=-1, plot=False, verbose=True,
                                rate_adjustment=True,
                                save_excel=False, excel_path=None
                                ):

    #TODO: output a plot which shows the topology and colors the critical components in red
    # TODO: fix normalization. failure and repair counts have to be normalized differently. Maybe remove repair counts for simplicity
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

        **plot**            - bool, whether to plot the graph

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

    # get converted graph datastructure (csr)
    conv = _graph_to_numba_arrays(G, sources, targets)

    edge_list = conv['edge_list']
    node_list = conv['node_list']
    n_edges = len(edge_list)
    n_nodes = len(node_list)

    lam_edges_arr = np.array([lam_edges[e] for e in conv['edge_list']], dtype=np.float64)
    lam_nodes_arr = np.array([lam_nodes[n] for n in conv['node_list']], dtype=np.float64)

    if mu_edges is None:
        mu_edges_arr = np.zeros(n_edges, dtype=np.float16)
    else:
        mu_edges_arr = np.array([mu_edges[e] for e in conv['edge_list']], dtype=np.float64)

    if mu_nodes is None:
        mu_nodes_arr = np.zeros(n_nodes, dtype=np.float16)
    else:
        mu_nodes_arr = np.array([mu_nodes[n] for n in conv['node_list']], dtype=np.float64)

    n_events = n_edges + n_nodes

    # Flatten and filter invalid values (-1)
    flat = all_critical.flatten()
    valid = flat[flat >= 0]

    if len(valid) == 0:
        print("No critical components tracked!")
        return None

    # Count occurrences
    unique_idx, counts = np.unique(valid, return_counts=True)

    # build array of counts (zero for components that never occurred)
    full_counts = np.zeros(n_events, dtype=np.float64)
    for idx, count in zip(unique_idx, counts):
        full_counts[idx] = count

    lam_all = np.concatenate([lam_edges_arr, lam_nodes_arr])
    mu_all  = np.concatenate([mu_edges_arr,  mu_nodes_arr])

    sum_lam_mu = lam_all + mu_all

    expected_rates = np.where(
        sum_lam_mu > 0,
        lam_all * mu_all / sum_lam_mu,
        0.0
    )

    if np.sum(expected_rates) < 1e-30:
        expected_rates = lam_all.copy()

    total_rate = np.sum(expected_rates)

    expected_fractions = (expected_rates / total_rate
                          if total_rate > 0
                          else np.ones(n_events) / n_events)

    # Criticality score
    total_observed = np.sum(full_counts)

    # get criticalities
    criticality = _calc_criticalities(n_events, total_observed, expected_fractions, full_counts, rate_adjustment)

    # slice array in critical edges and critical nodes
    edge_crit = criticality[:n_edges]
    node_crit = criticality[n_edges:]

    # sort arrays
    top_edge_idx = np.argsort(edge_crit)[::-1][:]   #[:top_n]
    top_node_idx = np.argsort(node_crit)[::-1][:]   #[:top_n]

    # Print results
    if verbose:
        _print_criticality(total_observed, criticality, top_n,
                           top_edge_idx, edge_list, edge_crit, n_edges,
                           top_node_idx, node_list, node_crit, full_counts)

    if plot:
        _critical_bar_plot(top_edge_idx, top_node_idx,
                       edge_crit, edge_list,
                       node_crit, node_list)

    if save_excel:
        _save_criticality_excel(
            total_observed, criticality, top_n,
            top_edge_idx, edge_list, edge_crit, n_edges,
            top_node_idx, node_list, node_crit, full_counts,
            excel_path,
        )

    return {
        'edge_criticality': edge_crit,
        'node_criticality': node_crit,
        'full_counts': full_counts,
        'total_observed': total_observed
    }

def empirical_reliability(T, samples):
    """
    Builds an empirical reliability function R and returns its value at timepoint T: R(T)=P(t>T).

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

    p_failure = n_failure / n
    reliability = n_survivor / n

    return reliability

# ----------------------------------------------------------------------------------------------------------------------
# Main API: run N Monte Carlo simulations and estimate reliability metrics from samples
# ----------------------------------------------------------------------------------------------------------------------
def estimate_mttf_mttr(G, sources, targets, min_connected=-1,
                       N=1000, depth=200, TOL=0,
                       max_time=np.inf, max_events=-1,
                       return_samples=True, analyze_crit=False, laziness=0,
                       use_numba=True, parallel=True):
    """
    Run N Monte Carlo simulations and estimate MTTF/MTTR.

    TODO: Remove max_events, laziness for release. remove TOL and return_samples until implemented.
    TODO: Check if N and depth can be collapsed to one argument

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

        **TOL**                 - float, tolerance for convergence of MTTF/MTTR (not yet implemented).

        **max_time**            - float, parameter to optimize sample collection for empirical reliability function type
                                  calculations.

        **max_events**          - int, control maximum number of events to avoid infinite loops for super-robust networks.

        **return_samples**      - Boolean, choose whether all samples should be returned, alongside the mean values.

        **analyze_crit**        - Boolean, choose whether network should be analyzed for critical components. (WIP)

        **laziness**            - float in [0,1), parameter which allows to sacrifice some accuracy for performance.
                                  Only checks the connectivity of the network if laziness*(V+E) events took place (only numba).

        **use_numba**           - Boolean, use Numba-optimized version if available (default: True)

        **parallel**            - Boolean, enable parallelization (default: True)

    :OUTPUT:
        {
        **mttf**                - float, mean time to failure

        **mttr**                - float, mean time to repair (np.inf if non-repairable)

        **mttf_samples**        - np.ndarray, mttf samples (None if not return_samples)

        **mttr_samples**        - np.ndarray, mttr samples (None if not return_samples or non-repairable)
        }
    """

    if max_time < np.inf:
        print('Warning: max_time Speedup is used. MTTF, MTTR might be meaningless.')

    sources, targets = _normalize_connection_pairs(sources, targets)

    # Catch if G is not connected at start.
    is_connected, error_msg = _check_initial_connectivity(G, sources, targets, min_connected)

    if not is_connected:
        print(f'Initial connectivity check failed: {error_msg}')
        print('Please fix topology!')
        return {'mttf': None, 'mttr': None, 'mttf_samples': None, 'mttr_samples': None}

    # Extract rates from graph
    lam_edges, lam_nodes, mu_edges, mu_nodes = _get_lam_mu_from_graph(G)

    # Check for non-repairable case
    is_nonrepairable = (all(mu == 0 for mu in mu_edges.values()) and all(mu == 0 for mu in mu_nodes.values()))
    is_repairable = not is_nonrepairable    # TODO: do more elegantly later

    # TODO: REMOVE is_nofailure
    # Check for no-failure case
    is_nofailure = (all(lam == 0 for lam in lam_edges.values()) and all(lam == 0 for lam in lam_nodes.values()))

    all_critical = None
    edge_criticality = None
    node_criticality = None

    # Check for no-failure case
    if is_nofailure:
        # TODO!
        print('not implemented')
        return {'mttf':np.inf, 'mttr':0.0, 'mttf_samples':None, 'mttr_samples':None}

    if use_numba and NUMBA_AVAILABLE:
        all_results, all_critical = _run_numba(G, sources, targets, min_connected, is_repairable,
                                               lam_edges, lam_nodes, mu_edges, mu_nodes,
                                               N, depth, TOL,
                                               max_time, max_events,
                                               return_samples, analyze_crit, laziness,
                                               parallel)

        #if analyze_crit and all_critical.size > 0:
            #crit_dict = analyze_critical_components(all_critical, G, sources, targets, lam_edges, lam_nodes, mu_edges, mu_nodes)

            #edge_criticality = crit_dict['edge_criticality']
            #node_criticality = crit_dict['node_criticality']

    else:
        # Python fallback
        print("Warning! Using deprecated python fallback. Consider using numba to get access to maintained version.")
        print(f"Using Python fallback ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

        sources = sources[0]
        targets = targets[0]

        all_results = _run_python(G, sources, targets, is_repairable, lam_edges, lam_nodes, mu_edges, mu_nodes, N, depth)

    # filter results
    valid_results = _filter_results(all_results, is_repairable)

    # unpack results
    mttf_samples = valid_results['mttf_samples']
    mttr_samples = valid_results['mttr_samples']

    # calc mean values
    mttf = 0.0 if mttf_samples is None else float(np.mean(mttf_samples))
    mttr = np.inf if mttr_samples is None else float(np.mean(mttr_samples))

    # return everything
    return {'mttf': mttf,
            'mttr': mttr,
            'mttf_samples': mttf_samples,
            'mttr_samples': mttr_samples,
            'edge_criticality': edge_criticality,
            'node_criticality': node_criticality,
            'all_critical': all_critical,}
