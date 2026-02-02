'''
Created on 22.12.2025
@author: fnuetz
'''

# main API
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from pandaict.reliability.reliability_utils import get_lam_mu_from_graph

# import python fallback
from pandaict.reliability.monte_carlo_python_fallback import (
        _simulate_python_repairable,
        _simulate_python_norepair
    )

# try importing wrappers for numba version
try:
    from pandaict.reliability.monte_carlo_numba_wrappers import (
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
# Helper functions TODO: maybe outsource later
# ----------------------------------------------------------------------------------------------------------------------
def _check_initial_connectivity(G, sources, targets, min_connected):
    """
    Checks initial connectivity for source-target pairs.

    :INPUT:
        **G**               - networkX graph, topology of network
        **sources**         - list of ints, identifier of source nodes
        **targets**         - list of ints, identifier of target nodes
        **min_connected**   - int, minimum number of source-target pairs required to be connected.

    :OUTPUT:
        (is_ok, error_message)
    """
    n_pairs = len(sources)

    # Validate nodes exist
    for s in sources:
        if s not in G:
            return False, f"Source '{s}' not found in graph"
    for t in targets:
        if t not in G:
            return False, f"Target '{t}' not found in graph"

    # Count connected pairs
    n_connected = 0
    disconnected_pairs = []

    # check connection for all pairs
    for i in range(n_pairs):
        if nx.has_path(G, sources[i], targets[i]):
            n_connected += 1
        else:
            disconnected_pairs.append((sources[i], targets[i]))

    if n_connected >= min_connected:
        return True, None
    else:
        return False, (f"Only {n_connected} of {n_pairs} pairs connected, "
                       f"but {min_connected} required. "
                       f"Disconnected: {disconnected_pairs[:3]}{'...' if len(disconnected_pairs) > 3 else ''}")

def _normalize_connection_pairs(source, target):
    """
    Normalizes source/target to index-arrays of the same length.

    Supported Formats:
        1. single nodes: source="S", target="T" -> [idx_S], [idx_T]
        2. lists of same length: source=["S1","S2"], target=["T","T"] -> [idx_S1,idx_S2], [idx_T,idx_T]
        3. broadcast: source=["S1","S2"], target="T" → [idx_S1,idx_S2], [idx_T,idx_T]

    :OUTPUT:
        **(source_indices, target_indices)**    - np.ndarray(dtype=int64)
    """
    # Normalize to lists
    if isinstance(source, (str, int, np.integer)):
        sources = [source]
    elif isinstance(source, np.ndarray):
        sources = source.tolist()
    else:
        sources = list(source)

    #
    if isinstance(target, (str, int, np.integer)):
        targets = [target]
    elif isinstance(target, np.ndarray):
        targets = target.tolist()
    else:
        targets = list(target)

    # broadcast
    if len(sources) == 1 and len(targets) > 1:
        sources = sources * len(targets)
    elif len(targets) == 1 and len(sources) > 1:
        targets = targets * len(sources)

    #
    if len(sources) != len(targets):
        raise ValueError(
            f"source und target have to have the same length of be broadcastable. "
            f"Got {len(sources)} sources and {len(targets)} targets."
        )

    return sources, targets


def _to_index_arrays(sources, targets, node_to_idx):
    """Converts lists of node-names to np.arrays containing node-indices."""
    source_indices = np.array([node_to_idx[s] for s in sources], dtype=np.int64)
    target_indices = np.array([node_to_idx[t] for t in targets], dtype=np.int64)
    return source_indices, target_indices


def graph_to_numba_arrays(G, source, target):
    """
    Convert NetworkX graph to Numba-compatible np.ndarrays.

    :INPUT:
        **G**      - networkx.Graph, topology of network
        **source** - string, classifying source node
        **target** - string, classifying target node

    :OUTPUT:
        {
        **n_nodes**     - int, number of nodes
        **n_edges**     - int, number of edges
        **adj_offsets** - np.ndarray, array describing the number of edges for each node
        **adj_nodes**   - np.ndarray, array of adjacent nodes to all nodes
        **adj_edges**   - np.ndarray, array of adjacent edges to all nodes
        **source_idx**  - int, index of source node
        **target_idx**  - int, index of target node
        **edge_list**   - np.ndarray, list of edges
        **node_list**   - np.ndarray, list of nodes
    }
    """
    node_list = list(G.nodes())
    edge_list = list(G.edges())
    n_nodes = len(node_list)
    n_edges = len(edge_list)

    is_directed = isinstance(G, nx.DiGraph)

    # Node index mapping
    node_to_idx = {n: i for i, n in enumerate(node_list)}

    # normalize to corresponding pairs
    source_indices, target_indices = _to_index_arrays(source, target, node_to_idx)

    # Edge arrays
    edge_u = np.empty(n_edges, dtype=np.int64)
    edge_v = np.empty(n_edges, dtype=np.int64)
    for i, (u, v) in enumerate(edge_list):
        edge_u[i] = node_to_idx[u]
        edge_v[i] = node_to_idx[v]

    # Build CSR adjacency structure
    if is_directed:
        # Directed: count only outgoing edges per node
        deg = np.zeros(n_nodes, dtype=np.int64)
        for u_i in edge_u:
            deg[u_i] += 1

    else:
        # Unidirected: count both directions
        deg = np.zeros(n_nodes, dtype=np.int64)
        for u_i, v_i in zip(edge_u, edge_v):
            deg[u_i] += 1
            deg[v_i] += 1

    # build offset array
    adj_offsets = np.empty(n_nodes + 1, dtype=np.int64)
    adj_offsets[0] = 0
    for i in range(n_nodes):
        adj_offsets[i + 1] = adj_offsets[i] + deg[i]

    total_adj = adj_offsets[n_nodes]
    adj_nodes = np.empty(total_adj, dtype=np.int64)
    adj_edges = np.empty(total_adj, dtype=np.int64)

    # Fill adjacency arrays
    cur = np.zeros(n_nodes, dtype=np.int64)

    if is_directed:
        # Directed: only add edge u->v
        for ei, (u_i, v_i) in enumerate(zip(edge_u, edge_v)):
            pos_u = adj_offsets[u_i] + cur[u_i]
            adj_nodes[pos_u] = v_i
            adj_edges[pos_u] = ei
            cur[u_i] += 1

    else:
        # Unidirected: add both directions
        for ei, (u_i, v_i) in enumerate(zip(edge_u, edge_v)):
            # Add edge u->v
            pos_u = adj_offsets[u_i] + cur[u_i]
            adj_nodes[pos_u] = v_i
            adj_edges[pos_u] = ei
            cur[u_i] += 1

            # Add edge v->u
            pos_v = adj_offsets[v_i] + cur[v_i]
            adj_nodes[pos_v] = u_i
            adj_edges[pos_v] = ei
            cur[v_i] += 1

    return {
        'n_nodes': n_nodes,
        'n_edges': n_edges,
        'adj_offsets': adj_offsets,
        'adj_nodes': adj_nodes,
        'adj_edges': adj_edges,
        'source_idx': source_indices,
        'target_idx': target_indices,
        'edge_list': edge_list,
        'node_list': node_list,
        'node_to_idx': node_to_idx
    }

# ----------------------------------------------------------------------------------------------------------------------
# Critical Component Analysis (Prototype)
# ----------------------------------------------------------------------------------------------------------------------
def analyze_critical_components(all_critical, n_edges, n_nodes,
                                edge_list, node_list,
                                lam_edges_arr, lam_nodes_arr,
                                mu_edges_arr, mu_nodes_arr,
                                top_n=10, plot=True, verbose=True, rate_adjustment=True):
    #TODO: validate function
    #TODO: output a plot which shows the topology and colors the critical components in red
    """

    Analyze which components are disproportionately critical by calculating the expected
    :INPUT:

        **all_critical**    - array of all critical components returned by monte_carlo (WIP)

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

        **verbose**         - bool,

        **rate_adjustment** - bool, choose whether to adjust the counts by their rates.
                              This determines whether the network is analyzed for bare topological
                              criticalities (True) or a wholistic analysis of critical components
                              is performed, which explicitly depends on the rates of the components (False).

    :OUTPUT:
        dict with edge_criticality, node_criticality, counts, plots, etc.

    """
    if top_n == 0:
        top_n = -1

    if mu_edges_arr is None:
        mu_edges_arr = np.zeros(n_edges, dtype=np.float16)

    if mu_nodes_arr is None:
        mu_nodes_arr = np.zeros(n_nodes, dtype=np.float16)

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
        if idx < n_events:
            full_counts[idx] = count

    # Normalize by expected rates (lam + mu)
    expected_rates = np.concatenate([
        lam_edges_arr + mu_edges_arr,
        lam_nodes_arr + mu_nodes_arr
    ])
    total_rate = np.sum(expected_rates)

    expected_fractions = expected_rates / total_rate if total_rate > 0 else np.ones(n_events) / n_events

    # Criticality score
    total_observed = np.sum(full_counts)
    criticality = np.zeros(n_events, dtype=np.float64)

    if total_observed > 0:
        for i in range(n_events):
            if rate_adjustment and expected_fractions[i] > 0:
                criticality[i] = (full_counts[i] / total_observed) / expected_fractions[i]
            elif not rate_adjustment:  # skip expected_fraction <= 0
                criticality[i] = (full_counts[i] / total_observed)

    # slice array in critical edges and critical nodes
    edge_crit = criticality[:n_edges]
    node_crit = criticality[n_edges:]

    # sort arrays
    top_edge_idx = np.argsort(edge_crit)[::-1][:top_n]
    top_node_idx = np.argsort(node_crit)[::-1][:top_n]

    # Print results
    if verbose:
        print("\n" + "=" * 70)
        print("CRITICAL COMPONENT ANALYSIS")
        print("=" * 70)
        print(f"Total events tracked: {int(total_observed)}")
        print("\nScore = Observed / Expected")
        print("  > 1.0: MORE critical")
        print("  ~ 1.0: As expected")
        print("  < 1.0: LESS critical")

        print(f"\n{'─' * 70}")
        if top_n > 0:
            print(f"TOP {top_n} CRITICAL EDGES")
        else:
            print(f"CRITICAL EDGES")
        print(f"{'─' * 70}")
        for rank, i in enumerate(top_edge_idx, 1):
            print(f"  {rank:2d}. {edge_list[i]}: Score={edge_crit[i]:.3f}, Count={int(full_counts[i])}")

        print(f"\n{'─' * 70}")
        if top_n > 0:
            print(f"TOP {top_n} CRITICAL NODES")
        else:
            print(f"CRITICAL NODES")
        print(f"{'─' * 70}")
        for rank, i in enumerate(top_node_idx, 1):
            print(f"  {rank:2d}. {node_list[i]}: Score={node_crit[i]:.3f}, Count={int(full_counts[n_edges + i])}")

    if plot:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

        edges_str = [f"{u}-{v}" for u, v in [edge_list[i] for i in top_edge_idx]]
        colors = ['red' if edge_crit[i] > 1.0 else 'gray' for i in top_edge_idx]
        ax1.barh(range(len(top_edge_idx)), edge_crit[top_edge_idx], color=colors, alpha=0.7)
        ax1.axvline(1.0, color='black', linestyle='--', lw=2)
        ax1.set_yticks(range(len(top_edge_idx)))
        ax1.set_yticklabels(edges_str)
        ax1.set_xlabel('Criticality Score')
        if top_n > 0:
            ax1.set_title(f'Top {top_n} Critical Edges')
            ax2.set_title(f'Top {top_n} Critical Nodes')
        else:
            ax1.set_title(f'Critical Edges')
            ax2.set_title(f'Critical Nodes')

        ax1.invert_yaxis()

        nodes_str = [str(node_list[i]) for i in top_node_idx]
        colors = ['red' if node_crit[i] > 1.0 else 'gray' for i in top_node_idx]
        ax2.barh(range(len(top_node_idx)), node_crit[top_node_idx], color=colors, alpha=0.7)
        ax2.axvline(1.0, color='black', linestyle='--', lw=2)
        ax2.set_yticks(range(len(top_node_idx)))
        ax2.set_yticklabels(nodes_str)
        ax2.set_xlabel('Criticality Score')

        ax2.invert_yaxis()

        plt.tight_layout()
        plt.show()

    return {
        'edge_criticality': edge_crit,
        'node_criticality': node_crit,
        'full_counts': full_counts,
        'total_observed': total_observed
    }

def empirical_reliability(T, samples):
    """
    Builds an empirical reliability function R and returns its value at timepoint T: R(T)=P(t>=T).

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
                       N=1000, depth=1, TOL=0,
                       max_time=np.inf, max_events=-1,
                       return_samples=False, analyze_crit=False, laziness=0,
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
    is_multi = len(sources) > 1

    # Catch if G is not connected at start.
    is_connected, error_msg = _check_initial_connectivity(G, sources, targets, min_connected)

    if not is_connected:
        print(f'Initial connectivity check failed: {error_msg}')
        print('Please fix topology!')
        if return_samples:
            return {'mttf': None, 'mttr': None, 'mttf_samples': None, 'mttr_samples': None}
        return {'mttf': None, 'mttr': None}

    # Extract rates from graph
    lam_edges, lam_nodes, mu_edges, mu_nodes = get_lam_mu_from_graph(G)

    # Check for non-repairable case
    is_nonrepairable = (all(mu == 0 for mu in mu_edges.values()) and all(mu == 0 for mu in mu_nodes.values()))

    # Check for no-failure case
    is_nofailure = (all(lam == 0 for lam in lam_edges.values()) and all(lam == 0 for lam in lam_nodes.values()))

    # Check for no-failure case
    if is_nofailure:
        # TODO!
        print('not implemented')

        if return_samples:
            return {'mttf':np.inf, 'mttr':0.0, 'mttf_samples':None, 'mttr_samples':None}
        return np.inf, 0.0

    if use_numba and NUMBA_AVAILABLE:
        # Convert graph to arrays
        conv = graph_to_numba_arrays(G, sources, targets)

        # get edge and node arrays
        lam_edges_arr = np.array([lam_edges[e] for e in conv['edge_list']], dtype=np.float64)
        lam_nodes_arr = np.array([lam_nodes[n] for n in conv['node_list']], dtype=np.float64)

        if is_nonrepairable:
            # non-repairable case
            if analyze_crit:
                # TODO: Implement analyze_crit for non-repairable nets
                print('Warning! non-repairable calculation does not support analyze_crit yet.')

            if parallel:
                print(f"Running {N} simulations in parallel...")
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
            # Filter results
            fail_inf_mask = np.isinf(all_results)
            n_fail_inf = int(np.sum(fail_inf_mask))

            nan_mask = np.isnan(all_results)
            n_nan = int(np.sum(nan_mask))

            finite_mask = np.isfinite(all_results)

            mttf_samples = all_results[finite_mask]
            #valid = all_results[~np.isnan(all_results)]

            if n_fail_inf > 0 or n_nan > 0:
                msg_parts = []
                if n_fail_inf > 0:
                    msg_parts.append(f"{n_fail_inf} simulation(s) reached max_events without system failure. "
                                     f"That speaks for a rather robust system which will likely never fail!")
                if n_nan > 0:
                    msg_parts.append(f"{n_nan} simulation(s) returned NaN (e.g. total_rate <= 0)")
                print("Warning: (Monte Carlo): " + "; ".join(msg_parts) +
                      ". These runs were excluded from MTTF/MTTR estimation.")

            if len(mttf_samples) == 0:
                print("Warning: No valid Monte Carlo samples (all runs either NaN or max_events timeout)")
                return {'mttf':None, 'mttr':None, 'mttf_samples':None, 'mttr_samples':None}

            if analyze_crit and all_critical.size > 0:
                print(all_critical.flatten())
                analyze_critical_components(
                    all_critical, conv['n_edges'], conv['n_nodes'],
                    conv['edge_list'], conv['node_list'],
                    lam_edges_arr, lam_nodes_arr,
                    None, None, plot=True
                )

            if return_samples:
                return {'mttf': float(np.mean(mttf_samples)),
                        'mttr': np.inf,
                        'mttf_samples': mttf_samples,
                        'mttr_samples': None}

            return {'mttf': float(np.mean(mttf_samples)),
                    'mttr': np.inf,
                    'mttf_samples': None,
                    'mttr_samples': None}

        else:
            # Repairable case
            mu_edges_arr = np.array([mu_edges[e] for e in conv['edge_list']], dtype=np.float64)
            mu_nodes_arr = np.array([mu_nodes[n] for n in conv['node_list']], dtype=np.float64)

            max_events = -1

            print(f"Running {N * depth} ({N} x {depth}) simulations {'in parallel' if parallel else ''}...")

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

            # filter results
            fail_inf_mask = np.isinf(all_results[:,0])
            repair_inf_mask = np.isinf(all_results[:,1])

            n_fail_inf = int(np.sum(fail_inf_mask))
            n_repair_inf = int(np.sum(repair_inf_mask))

            nan_mask = np.isnan(all_results[:,0]) | np.isnan(all_results[:,1])
            n_nan = int(np.sum(nan_mask))

            finite_mask = np.isfinite(all_results[:,0]) & np.isfinite(all_results[:,1])

            mttf_samples = all_results[finite_mask, 0]
            mttr_samples = all_results[finite_mask, 1]

            if n_fail_inf > 0 or n_repair_inf > 0 or n_nan > 0:
                msg_parts = []
                if n_fail_inf > 0:
                    msg_parts.append(f"{n_fail_inf} simulation(s) reached max_events without system failure. "
                                     f"That speaks for a rather robust system which will likely never fail!")
                if n_repair_inf > 0:
                    msg_parts.append(f"{n_repair_inf} simulation(s) reached max_events without system repair. "
                                     f"That speaks for a rather fragile system which likely can never be repaired!")
                if n_nan > 0:
                    msg_parts.append(f"{n_nan} simulation(s) returned NaN (e.g. total_rate <= 0)")
                print("Warning: (Monte Carlo): " + "; ".join(msg_parts) +
                      ". These runs were excluded from MTTF/MTTR estimation.")

            if len(mttf_samples) == 0:
                print("Warning: No valid Monte Carlo samples (all runs either NaN or max_events timeout)")

                return {'mttf': None, 'mttr': None, 'mttf_samples': None, 'mttr_samples': None}

            if analyze_crit and all_critical.size > 0:
                analyze_critical_components(
                    all_critical, conv['n_edges'], conv['n_nodes'],
                    conv['edge_list'], conv['node_list'],
                    lam_edges_arr, lam_nodes_arr,
                    mu_edges_arr, mu_nodes_arr, plot=True
                )

            if return_samples:
                return {'mttf': float(np.mean(mttf_samples)),
                        'mttr': float(np.mean(mttr_samples)),
                        'mttf_samples': mttf_samples,
                        'mttr_samples': mttr_samples}


            return {'mttf': float(np.mean(mttf_samples)),
                    'mttr': float(np.mean(mttr_samples)),
                    'mttf_samples': None,
                    'mttr_samples': None}

    # Python fallback
    print(f"Warning! Using deprecated python fallback. Consider using numba to get access to maintained version.")
    print(f"Using Python fallback ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

    if is_multi:
        # TODO
        print("Warning! Python Fallback does not support multi-source-target scenarios.")

    sources = sources[0]
    targets = targets[0]

    if is_nonrepairable:
        samples = [_simulate_python_norepair(G, sources, targets, lam_edges, lam_nodes) for _ in range(N)]
        if return_samples:
            return {'mttf': float(np.mean(samples)),
                    'mttr': np.inf,
                    'mttf_samples': samples,
                    'mttr_samples': None}

        return {'mttf': float(np.mean(samples)),
                'mttr': np.inf,
                'mttf_samples': None,
                'mttr_samples': None}
    else:
        results = []
        for _ in range(N):
            res = _simulate_python_repairable(G, sources, targets, lam_edges, lam_nodes,
                                              mu_edges, mu_nodes, depth)
            if res is not None:
                results.append(res)

        if not results:
            return {'mttf': None,
                    'mttr': None,
                    'mttf_samples': None,
                    'mttr_samples': None}

        # TODO: filter results
        mttf_samples = [r[0] for r in results]
        mttr_samples = [r[1] for r in results]

        if return_samples:
            return {'mttf': float(np.mean(mttf_samples)),
                    'mttr': float(np.mean(mttr_samples)),
                    'mttf_samples': mttf_samples,
                    'mttr_samples': mttr_samples}


        return {'mttf': float(np.mean(mttf_samples)),
                'mttr': float(np.mean(mttr_samples)),
                'mttf_samples': None,
                'mttr_samples': None}