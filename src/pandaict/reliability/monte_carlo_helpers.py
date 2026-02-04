'''
Created on 04.02.2026
@author: fnuetz
'''

import networkx as nx
import numpy as np

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
    # Normalize source to list
    if isinstance(source, (str, int, np.integer)):
        sources = [source]
    elif isinstance(source, np.ndarray):
        sources = source.tolist()
    else:
        sources = list(source)

    # Normalize target to list
    if isinstance(target, (str, int, np.integer)):
        targets = [target]
    elif isinstance(target, np.ndarray):
        targets = target.tolist()
    else:
        targets = list(target)

    # broadcast sources onto targets or targets onto sources
    if len(sources) == 1 and len(targets) > 1:
        sources = sources * len(targets)
    elif len(targets) == 1 and len(sources) > 1:
        targets = targets * len(sources)

    # catch
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


def _graph_to_numba_arrays(G, source, target):
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

def _filter_results(all_results, is_repairable):
    """Filter out invalid results from all_results"""
    # TODO: write less repetitive

    if is_repairable:
        # filter results
        fail_inf_mask = np.isinf(all_results[:, 0])
        repair_inf_mask = np.isinf(all_results[:, 1])

        n_fail_inf = int(np.sum(fail_inf_mask))
        n_repair_inf = int(np.sum(repair_inf_mask))

        nan_mask = np.isnan(all_results[:, 0]) | np.isnan(all_results[:, 1])
        n_nan = int(np.sum(nan_mask))

        finite_mask = np.isfinite(all_results[:, 0]) & np.isfinite(all_results[:, 1])

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

    else:
        # Filter results
        fail_inf_mask = np.isinf(all_results)
        n_fail_inf = int(np.sum(fail_inf_mask))

        nan_mask = np.isnan(all_results)
        n_nan = int(np.sum(nan_mask))

        finite_mask = np.isfinite(all_results)

        mttf_samples = all_results[finite_mask]
        mttr_samples = None

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
        return {'mttf_samples': None, 'mttr_samples': None}

    return {'mttf_samples': mttf_samples, 'mttr_samples': mttr_samples}
