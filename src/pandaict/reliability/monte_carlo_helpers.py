'''
Created on 04.02.2026
@author: fnuetz

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

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
        3. broadcast: source=["S1","S2"], target="T" -> [idx_S1,idx_S2], [idx_T,idx_T]

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

def _inf_warning(data, event_name, explanation):
    """Return warning string if data contains inf values, else None."""
    n_inf = int(np.sum(np.isinf(data)))
    if n_inf > 0:
        return (f"{n_inf} simulation(s) reached max_events without {event_name}. \n"
                f"         That speaks for {explanation}!")
    return None


def _filter_results(all_results, is_repairable, max_time):
    """Filter out invalid results (inf/NaN) from simulation output."""

    if is_repairable:
        fail_data, repair_data = all_results[:, 0], all_results[:, 1]
        finite_mask = np.isfinite(fail_data) & np.isfinite(repair_data)
        n_nan = int(np.sum(np.isnan(fail_data) | np.isnan(repair_data)))

        warnings = [
            _inf_warning(fail_data, "system failure",
                         "a rather robust system which will likely never fail"),
            _inf_warning(repair_data, "system repair",
                         "a rather fragile system which likely can never be repaired"),
        ]
        mttf_samples = all_results[finite_mask, 0]
        mttr_samples = all_results[finite_mask, 1]

    else:
        finite_mask = np.isfinite(all_results)
        n_nan = int(np.sum(np.isnan(all_results)))

        warnings = [
            _inf_warning(all_results, "system failure",
                         "a rather robust system which will likely never fail"),
        ]
        mttf_samples = all_results[finite_mask]
        mttr_samples = None

    # NaN warning (shared for both)
    if n_nan > 0:
        warnings.append(f"{n_nan} simulation(s) returned NaN (e.g. total_rate <= 0)")

    # Print all collected warnings in one go
    msg_parts = [w for w in warnings if w is not None]

    # only warn if max_time speedup is *not* used!
    if msg_parts and max_time == np.inf:
        print("Warning: " + "; ".join(msg_parts)+ " \n"
              "         These runs were excluded from MTTF/MTTR estimation.")

    if len(mttf_samples) == 0 and max_time == np.inf:
        print("Warning: No valid Monte Carlo samples "
              "(all runs either NaN or max_events timeout without outage)")
        return {'mttf_samples': None, 'mttr_samples': None}
    
    elif len(mttf_samples) == 0 and max_time < np.inf:
        print("Info: No finite samples were collected "
              "(all runs either reached T or max_events timeout without outage)")
        return {'mttf_samples': None, 'mttr_samples': None}

    return {'mttf_samples': mttf_samples, 'mttr_samples': mttr_samples}


def _critical_bar_plot(top_edge_idx, top_node_idx,
                       edge_crit, edge_labels,
                       node_crit, node_labels,
                       rate_adjustment):

    n_rows = max(len(top_edge_idx), len(top_node_idx)) + 1
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, max(3, int(n_rows / 4)))) # dynamic height based on number of critical components

    # === EDGES ===
    if len(top_edge_idx) > 0 and np.any(edge_crit[top_edge_idx] > 0):
        edges_str = [edge_labels.get(i, f"Edge {i}") for i in top_edge_idx]
        colors = ['red' if edge_crit[i] > 1.01 else 'gray' for i in top_edge_idx]
        ax1.barh(range(len(top_edge_idx)), edge_crit[top_edge_idx], color=colors, alpha=0.7)

        max_edge_val = np.nanmax(edge_crit[top_edge_idx])
        ax1.set_xlim(0, max(max_edge_val * 1.2, 1.5))
        if rate_adjustment:
            ax1.set_xlabel('Topological Criticality Score')
        else:
            ax1.set_xlabel('Wholistic Criticality Score')
        ax1.axvline(1.0, color='black', linestyle='--', lw=2)
        ax1.set_yticks(range(len(top_edge_idx)))
        ax1.set_yticklabels(edges_str)
    else:
        ax1.text(0.5, 0.5, 'No critical edges', ha='center', va='center',
                 transform=ax1.transAxes, fontsize=12, color='gray')
        ax1.set_xlim(0, 2)  # avoids singular matrix error

    ax1.set_title('Critical Edges')
    ax1.invert_yaxis()

    # === NODES ===
    if len(top_node_idx) > 0 and np.any(node_crit[top_node_idx] > 0):
        nodes_str = [node_labels.get(i, f"Node {i}") for i in top_node_idx]
        colors = ['red' if node_crit[i] > 1.01 else 'gray' for i in top_node_idx]
        ax2.barh(range(len(top_node_idx)), node_crit[top_node_idx], color=colors, alpha=0.7)

        max_node_val = np.nanmax(node_crit[top_node_idx])
        ax2.set_xlim(0, max(max_node_val * 1.2, 1.5))
        if rate_adjustment:
            ax2.set_xlabel('Topological Criticality Score')
        else:
            ax2.set_xlabel('Wholistic Criticality Score')

        ax2.axvline(1.0, color='black', linestyle='--', lw=2)

        ax2.set_yticks(range(len(top_node_idx)))
        ax2.set_yticklabels(nodes_str)
    else:
        ax2.text(0.5, 0.5, 'No critical nodes', ha='center', va='center',
                 transform=ax2.transAxes, fontsize=12, color='gray')
        ax2.set_xlim(0, 2)


    ax2.set_title('Critical Nodes')
    ax2.invert_yaxis()

    if rate_adjustment:
        fig.suptitle('Topological Criticality Analysis')
    else:
        fig.suptitle('Wholistic Criticality Analysis')

    plt.tight_layout()
    plt.show()


def _print_criticality(total_observed, total_failure, total_repair, top_n,
                       top_edge_fail_idx, top_edge_rep_idx, edge_list,
                       edge_fail_crit, edge_rep_crit, n_edges,
                       top_node_fail_idx, top_node_rep_idx, node_list,
                       node_fail_crit, node_rep_crit, n_nodes,
                       failure_counts, repair_counts,
                       edge_labels=None, node_labels=None):
    print("\n" + "=" * 70)
    print("CRITICAL COMPONENT ANALYSIS")
    print("=" * 70)
    print(f"Total events tracked:  {int(total_observed)}")
    print(f"  - Failure events:   {int(total_failure)}")
    print(f"  - Repair events:    {int(total_repair)}")

    print("\nScore = Observed / Expected")
    print("  > 1.0: MORE critical than expected (topologically)")
    print("  ~ 1.0: As expected from rates alone")
    print("  < 1.0: LESS critical than expected")

    n_show = top_n if top_n > 0 else n_edges

    # Failure-Critical Edges
    print(f"\n{'─' * 70}")
    print("FAILURE-CRITICAL EDGES  (last straw before System Down)")
    print(f"{'─' * 70}")
    for rank, i in enumerate(top_edge_fail_idx[:n_show], 1):
        print(f"  {rank:2d}. {edge_labels.get(i, str(edge_list[i])) if edge_labels else str(edge_list[i])}: "
              f"Score={edge_fail_crit[i]:.3f}, "
              f"Count={int(failure_counts[i])}")

    # Failure-Critical Nodes
    n_show_n = top_n if top_n > 0 else n_nodes
    print(f"\n{'─' * 70}")
    print("FAILURE-CRITICAL NODES  (last straw before System Down)")
    print(f"{'─' * 70}")
    for rank, i in enumerate(top_node_fail_idx[:n_show_n], 1):
        print(f"  {rank:2d}. {node_labels.get(i, str(node_list[i])) if node_labels else str(node_list[i])}: "
              f"Score={node_fail_crit[i]:.3f}, "
              f"Count={int(failure_counts[n_edges + i])}")

    if total_repair > 0:
        # Repair-Critical Edges
        print(f"\n{'─' * 70}")
        print("REPAIR-CRITICAL EDGES  (last straw before System Up)")
        print(f"{'─' * 70}")
        for rank, i in enumerate(top_edge_rep_idx[:n_show], 1):
            print(f"  {rank:2d}. {edge_labels.get(i, str(edge_list[i])) if edge_labels else str(edge_list[i])}: "
                  f"Score={edge_rep_crit[i]:.3f}, "
                  f"Count={int(repair_counts[i])}")

        # Repair-Critical Nodes
        print(f"\n{'─' * 70}")
        print("REPAIR-CRITICAL NODES  (last straw before System Up)")
        print(f"{'─' * 70}")
        for rank, i in enumerate(top_node_rep_idx[:n_show_n], 1):
            print(f"  {rank:2d}. {node_labels.get(i, str(node_list[i])) if node_labels else str(node_list[i])}: "
                  f"Score={node_rep_crit[i]:.3f}, "
                  f"Count={int(repair_counts[n_edges + i])}")


def _calc_criticalities(n_events, total_observed, expected_fractions, full_counts, rate_adjustment):
    # init criticality array
    criticality = np.zeros(n_events, dtype=np.float64)

    # loop over
    if total_observed > 0:
        for i in range(n_events):
            if rate_adjustment and expected_fractions[i] > 0:
                criticality[i] = (full_counts[i] / total_observed) / expected_fractions[i]
            elif not rate_adjustment:  # skip expected_fraction <= 0
                criticality[i] = (full_counts[i] / total_observed)

    # normalize
    if not rate_adjustment:
        crit_mask = criticality > 0
        n_rel_comp = np.sum(crit_mask)
        criticality *= n_rel_comp

    return criticality


def _save_criticality_excel(total_observed, criticality, top_n,
                            top_edge_idx, edge_list, edge_crit, n_edges,
                            top_node_idx, node_list, node_crit, full_counts,
                            excel_path=None,
                            edge_labels=None, node_labels=None):
    """
    Writes the critical-component analysis to an Excel file.

    Sheets
    ------
    - **Summary**        : total events, score norm, interpretation key
    - **Critical Edges** : ranked table  (Rank, Edge, Score, Count)
    - **Critical Nodes** : ranked table  (Rank, Node, Score, Count)

    The content mirrors the console output of ``_print_criticality``.
    """

    # resolve output path
    if excel_path is None:
        filepath = Path.cwd() / "critical_components_analysis.xlsx"
    else:
        filepath = Path(excel_path)
        # if the user only gave a directory, append a default file name
        if filepath.is_dir():
            filepath = filepath / "critical_components_analysis.xlsx"

    filepath.parent.mkdir(parents=True, exist_ok=True)

    # how many rows to export
    n_show_edges = top_n if top_n > 0 else len(top_edge_idx)
    n_show_nodes = top_n if top_n > 0 else len(top_node_idx)

    # Sheet 1: Summary
    summary_rows = [
        ("Total events tracked", int(total_observed)),
        ("Score norm (sum)",     float(np.sum(criticality))),
        ("",                     ""),
        ("Score interpretation", ""),
        ("> 1.0",               "MORE critical than expected"),
        ("~ 1.0",               "As expected"),
        ("< 1.0",               "LESS critical than expected"),
    ]
    summary_df = pd.DataFrame(summary_rows, columns=["Parameter", "Value"])

    # Sheet 2: Critical Edges
    edge_rows = []
    for rank, i in enumerate(top_edge_idx[:n_show_edges], 1):
        edge_rows.append({
            "Rank":  rank,
            "Edge":  edge_labels.get(i, str(edge_list[i])) if edge_labels else str(edge_list[i]),
            "Score": round(float(edge_crit[i]), 4),
            "Count": int(full_counts[i]),
        })
    edge_df = pd.DataFrame(edge_rows)

    # Sheet 3: Critical Nodes
    node_rows = []
    for rank, i in enumerate(top_node_idx[:n_show_nodes], 1):
        node_rows.append({
            "Rank":  rank,
            "Node":  node_labels.get(i, str(node_list[i])) if node_labels else str(node_list[i]),
            "Score": round(float(node_crit[i]), 4),
            "Count": int(full_counts[n_edges + i]),
        })
    node_df = pd.DataFrame(node_rows)

    # write to excel
    with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Summary",         index=False)
        edge_df.to_excel(   writer, sheet_name="Critical Edges",  index=False)
        node_df.to_excel(   writer, sheet_name="Critical Nodes",  index=False)

    print(f"  -> Excel saved: {filepath}")