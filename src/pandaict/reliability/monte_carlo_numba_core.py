'''
Created on 22.12.2025
@author: fnuetz
'''

import numpy as np
from numba import njit

# ------------------------------------------------------------------------------------------------------------------
# Fenwick Tree (Binary Indexed Tree): Efficient datastructure for sampling of events
# ------------------------------------------------------------------------------------------------------------------
@njit
def bit_update(bit, idx, delta):
    """
    Update Fenwick Tree: add delta to position idx
    Propagate the change through all nodes in the tree which contain idx.

    :INPUT:
        **bit**     - Fenwick Tree
        **idx**     - index of change
        **delta**   - float, delta in total

    :OUTPUT:
        **bit**     - updated Fenwick Tree
    """
    n = bit.shape[0] - 1
    i = idx + 1  # 1-based indexing
    while i <= n:
        bit[i] += delta
        i += i & -i  # next index to update


@njit
def bit_build_from_array(arr):
    """
    Build Fenwick Tree from array of rates.
    :INPUT:
        **array**   - np.ndarray, containing all transition rates
    :OUTPUT:
        **bit**     - Fenwick Tree Array (Binary Indexed Tree)
    """
    n = arr.shape[0]
    bit = np.zeros(n + 1, dtype=np.float64)
    for i in range(n):
        bit[i + 1] = arr[i]
    # Propagate values up the tree
    for i in range(1, n + 1):
        j = i + (i & -i)
        if j <= n:
            bit[j] += bit[i]
    return bit


@njit
def bit_prefix_sum(bit, idx):
    """Get sum of elements in bit up to idx ~ sum(arr[0:idx])"""
    s = 0.0
    i = idx + 1
    while i > 0:
        s += bit[i]
        i -= i & -i  # parent in tree
    return s


@njit
def bit_find_index(bit, value):
    """
    Replaces old naive event sampling algorithm.
    Find smallest idx such that prefix_sum(idx) >= value.
    Binary search on Fenwick Tree: O(log n) instead of old O(n)
    """
    n = bit.shape[0] - 1
    idx = 0
    bitmask = 1
    # Find highest power of 2 <= n
    while bitmask * 2 <= n:
        bitmask *= 2
    # Binary search
    while bitmask != 0:
        t = idx + bitmask
        if t <= n and bit[t] < value:
            idx = t
            value -= bit[t]
        bitmask //= 2
    return idx  # 0-based


@njit
def _build_rates_and_bit(n_edges, n_nodes, lam_edges_arr, lam_nodes_arr):
    """Build rates array and Fenwick Tree from lam_edges_arr and lam_nodes_arr."""
    n_events = n_edges + n_nodes
    rates = np.empty(n_events, dtype=np.float64)

    # Initial rates = failure rates (all components start UP)
    for i in range(n_edges):
        rates[i] = lam_edges_arr[i]
    for j in range(n_nodes):
        rates[n_edges + j] = lam_nodes_arr[j]

    bit = bit_build_from_array(rates)
    return bit


# ------------------------------------------------------------------------------------------------------------------
# DFS Connectivity Check
# ------------------------------------------------------------------------------------------------------------------
@njit
def check_connections(adj_offsets, adj_nodes, adj_edges, edge_state, node_state,
                      source_indices, target_indices, min_connected=-1):
    """
    Checks connectivity for source-target pairs.
    System is UP if at least min_connected pairs are connected.

    :INPUT:
        **adj_offset, adj_nodes, adj_edges**    - np.ndarrays, topology of graph in csr format
        **edge_state, node_state**              - np.ndarrays(dtype=bool_), states of network components
        **source_indices**                      - np.ndarray(dtype=int64), source node indices
        **target_indices**                      - np.ndarray(dtype=int64), target node indices (same length)
        **min_connected**                       - int, minimum number of connected pairs required
            - min_connected=1: At least 1 pair (old require_all=False)
            - min_connected=k: At least k pairs (k-out-of-n)
            - min_connected=-1: All pairs (default) (old require_all=True)

    :OUTPUT: True if at least min_connected pairs are connected, False otherwise
    """
    n_pairs = source_indices.shape[0]

    # Clamp min_connected to valid range
    if min_connected == -1:
        min_connected = n_pairs
    elif min_connected < 1:
        min_connected = 1
    if min_connected > n_pairs:
        min_connected = n_pairs

    n_connected = 0
    n_remaining = n_pairs

    # check connectivity of pairs
    for i in range(n_pairs):
        s_idx = source_indices[i]
        t_idx = target_indices[i]

        if dfs_connected(adj_offsets, adj_nodes, adj_edges, edge_state, node_state, s_idx, t_idx):
            n_connected += 1

            # Early exit: Already enough connected
            if n_connected >= min_connected:
                return True

        n_remaining -= 1

        # Early exit: Can't reach min_connected anymore
        if n_connected + n_remaining < min_connected:
            return False

    return n_connected >= min_connected


@njit
def dfs_connected(adj_offsets, adj_nodes, adj_edges, edge_state, node_state,
                  source_idx, target_idx):
    """
    Depth First Search to determine connectivity between source_idx and target_idx (replaces slow NetworkX method)
    Check if source and target are connected via DFS.
    Returns True if connected, False otherwise.

    :INPUT:
        **adj_offset, adj_nodes, adj_edges**    - np.ndarrays, topology of graph in csr format
        **edge_state, node_state**              - np.ndarrays, states of network components
        **source_idx, target_idx**              - integers, indices of source and target nodes
    """
    # get number of nodes
    n = adj_offsets.shape[0] - 1

    # Check if source/target are active (enabling early checkout)
    if node_state[source_idx] == 0 or node_state[target_idx] == 0:
        return False

    if source_idx == target_idx:
        return True

    # DFS using stack
    visited = np.zeros(n, dtype=np.int8)
    stack = np.empty(n, dtype=np.int64)
    top = 0

    # Start from source
    stack[top] = source_idx
    top += 1
    visited[source_idx] = 1

    while top > 0:
        top -= 1
        u = stack[top]

        # Found target?
        if u == target_idx:
            return True

        # Explore neighbors
        start = adj_offsets[u]
        end = adj_offsets[u + 1]
        for p in range(start, end):
            v = adj_nodes[p]
            eidx = adj_edges[p]

            # Check if neighbor is reachable
            if visited[v] == 0 and node_state[v] == 1 and edge_state[eidx] == 1:
                visited[v] = 1
                stack[top] = v
                top += 1

    return False


# ------------------------------------------------------------------------------------------------------------------
# Core Simulation Loops
# ------------------------------------------------------------------------------------------------------------------
@njit
def simulate_numba_core(n_edges, n_nodes,
                        adj_offsets, adj_nodes, adj_edges,
                        source_idx, target_idx, min_connected,
                        lam_edges_arr, lam_nodes_arr,
                        mu_edges_arr, mu_nodes_arr, bit,
                        depth, max_events=-1, laziness=0, track_crit=True):
    """
    Core simulation loop in Numba which simulates UP->DOWN - cycles for depth deep.
    Returns array of (t_fail, t_repair) for each cycle.
    :INPUT:
        **n_edges, n_nodes**                    - ints, number of edges and nodes in network
        **adj_offsets, adj_nodes, adj_edges**   - np.ndarrays, topology of graph in csr format
        **source_idx, target_idx**              - np.ndarrays, indices of source(s) and target(s)
        **min_connected**                       - int, minimum number of connected pairs required
            - min_connected=1: At least 1 pair (old require_all=False)
            - min_connected=k: At least k pairs (k-out-of-n)
            - min_connected=-1: All pairs (default) (old require_all=True)
        **lam_edges_arr, lam_nodes_arr**        - np.ndarrays, failure rates of edges and nodes
        **mu_edges_arr, mu_nodes_arr**          - np.ndarrays, repair rates of edges and nodes
        **bit**                                 - Fenwick Tree Array, containing initial rates
        **depth**                               - int, number of cycles to be simulated on the semi-fixed network
        **max_events**                          - float, maximum simulation time, to avoid infinite loops
        **laziness**                            - float, between 0 and 1. Percentage by which the network has to
                                                  change before connectivity is checked again.
    :OUTPUT:
        **results**                             - np.ndarray of (t_fail, t_repair) for each cycle
    """

    # Initialize states (all UP)
    edge_state = np.ones(n_edges, dtype=np.bool_)
    node_state = np.ones(n_nodes, dtype=np.bool_)

    # get total number of possible events
    n_events = n_edges + n_nodes

    if max_events == -1:
        max_events = n_events * 200  # stop loop if the whole network has changed 50 times

    total_rate = bit_prefix_sum(bit, n_events - 1)

    # Results storage
    results = np.empty((depth, 2), dtype=np.float64)
    cycle_idx = 0

    if laziness < 0:
        print('Choose Values in [0,1) for Laziness')
        laziness = 0

    # threshold after which connectivity is checked again
    event_threshold = int(laziness * n_events)

    if track_crit:
        # preallocate array for the identification of critical components. (-1 = invalid)
        critical_components = np.full(2 * (event_threshold + 1) * depth, -1, dtype=np.int32)
    else:
        critical_components = np.empty(0, dtype=np.int32)

    crit_idx = 0
    crit_checkpoint = 0  # position on last successful check

    # Main cycle loop
    while cycle_idx < depth:

        # === PHASE 1: UP -> DOWN (run until failure) ===
        t_fail = 0.0
        connected = check_connections(adj_offsets, adj_nodes, adj_edges,
                                      edge_state, node_state,
                                      source_idx, target_idx, min_connected)

        # keep track of event number (lazy connectivity)
        event_count = -1

        # keep track of event id (max_events)
        event_idx = 0

        while connected:
            if total_rate <= 0.0:
                return results[:cycle_idx], critical_components[:crit_idx]  # failure

            # Sample time to next event
            dt = np.random.exponential(1.0 / total_rate)
            t_fail += dt
            if event_idx >= max_events:
                results[cycle_idx, 0] = np.inf
                results[cycle_idx, 1] = 0.0
                cycle_idx += 1
                return results[:cycle_idx], critical_components[:crit_idx]  # failure

            # Sample event using Fenwick Tree (O(log n))
            r = np.random.random() * total_rate
            idx = bit_find_index(bit, r)

            # Apply event
            if idx < n_edges:
                # Edge event
                e = idx
                old = edge_state[e]
                new = 1 - old
                edge_state[e] = new

                # Update rate
                old_rate = lam_edges_arr[e] if old == 1 else mu_edges_arr[e]
                new_rate = lam_edges_arr[e] if new == 1 else mu_edges_arr[e]
                delta = new_rate - old_rate

                # Update Fenwick Tree (O(log n))
                bit_update(bit, idx, delta)
                total_rate += delta
            else:
                # Node event
                ni = idx - n_edges
                old = node_state[ni]
                new = 1 - old
                node_state[ni] = new

                old_rate = lam_nodes_arr[ni] if old == 1 else mu_nodes_arr[ni]
                new_rate = lam_nodes_arr[ni] if new == 1 else mu_nodes_arr[ni]
                delta = new_rate - old_rate

                bit_update(bit, idx, delta)
                total_rate += delta

            # increment event counters
            event_count += 1
            event_idx += 1

            # store last event
            if track_crit:
                critical_components[crit_idx] = idx
                crit_idx += 1

            # Lazy connectivity check
            if event_count >= event_threshold:
                connected = check_connections(adj_offsets, adj_nodes, adj_edges,
                                              edge_state, node_state,
                                              source_idx, target_idx, min_connected)
                if track_crit:
                    if connected:
                        # still connected -> not critical -> overwrite values by reseting writer
                        crit_idx = crit_checkpoint
                    else:
                        # disconnected -> components are critical -> update crit_checkpoint
                        crit_checkpoint = crit_idx

                # reset event_count
                event_count = -1

        # === PHASE 2: DOWN → UP (run until repair) ===
        t_repair = 0.0
        event_count = -1
        event_idx = 0

        if track_crit:
            crit_checkpoint = crit_idx

        connected = check_connections(adj_offsets, adj_nodes, adj_edges,
                                      edge_state, node_state,
                                      source_idx, target_idx, min_connected)

        while not connected:
            if total_rate <= 0.0:
                return results[:cycle_idx], critical_components[:crit_idx]

            dt = np.random.exponential(1.0 / total_rate)
            t_repair += dt
            if event_idx >= max_events:
                results[cycle_idx, 0] = t_fail
                results[cycle_idx, 1] = np.inf
                cycle_idx += 1
                return results[:cycle_idx], critical_components[:crit_idx]

            r = np.random.random() * total_rate
            idx = bit_find_index(bit, r)

            if idx < n_edges:
                e = idx
                old = edge_state[e]
                new = 1 - old
                edge_state[e] = new
                old_rate = lam_edges_arr[e] if old == 1 else mu_edges_arr[e]
                new_rate = lam_edges_arr[e] if new == 1 else mu_edges_arr[e]
                delta = new_rate - old_rate
                bit_update(bit, idx, delta)
                total_rate += delta
            else:
                ni = idx - n_edges
                old = node_state[ni]
                new = 1 - old
                node_state[ni] = new
                old_rate = lam_nodes_arr[ni] if old == 1 else mu_nodes_arr[ni]
                new_rate = lam_nodes_arr[ni] if new == 1 else mu_nodes_arr[ni]
                delta = new_rate - old_rate
                bit_update(bit, idx, delta)
                total_rate += delta

            if track_crit:
                critical_components[crit_idx] = idx
                crit_idx += 1

            # increment event counters
            event_count += 1
            event_idx += 1

            if event_count >= event_threshold:
                connected = check_connections(adj_offsets, adj_nodes, adj_edges,
                                              edge_state, node_state,
                                              source_idx, target_idx, min_connected)
                if track_crit:
                    if not connected:
                        # still disconnected -> not critical -> overwrite values by reseting writer
                        crit_idx = crit_checkpoint
                    else:
                        # connected again -> components are critical -> update crit_checkpoint
                        crit_checkpoint = crit_idx

                # reset event_count
                event_count = -1

        # Store results
        results[cycle_idx, 0] = t_fail
        results[cycle_idx, 1] = t_repair
        cycle_idx += 1

    return results, critical_components[:crit_idx]


@njit
def simulate_numba_core_norepair(n_edges, n_nodes,
                                 adj_offsets, adj_nodes, adj_edges,
                                 source_idx, target_idx, min_connected,
                                 lam_edges_arr, lam_nodes_arr, bit):
    """
    Simulate system lifetime for a non-repairable system (µ=0).
    :INPUT:
        **n_edges, n_nodes**                    - ints, number of edges and nodes in network
        **adj_offsets, adj_nodes, adj_edges**   - np.ndarrays, topology of graph in csr format
        **source_idx, target_idx**              - integers, indices of source and target nodes
        **min_connected**                       - int, minimum number of connected pairs required
            - min_connected=1: At least 1 pair (old require_all=False)
            - min_connected=k: At least k pairs (k-out-of-n)
            - min_connected=-1: All pairs (default) (old require_all=True)
        **lam_edges_arr, lam_nodes_arr**        - np.ndarrays, failure rates of edges and nodes
        **bit**                                 - Fenwick Tree, containing relevant rates for sampling of events

    :OUTPUT:
        **t** - float, time until first system failure (MTTF sample)
    """

    # Initialize states (all UP)
    edge_state = np.ones(n_edges, dtype=np.bool_)
    node_state = np.ones(n_nodes, dtype=np.bool_)

    # Build event list
    n_events = n_edges + n_nodes

    total_rate = bit_prefix_sum(bit, n_events - 1)

    t = 0.0

    # Run until disconnected
    while True:
        # Check connectivity
        connected = check_connections(adj_offsets, adj_nodes, adj_edges,
                                      edge_state, node_state,
                                      source_idx, target_idx, min_connected)

        if not connected:
            # System failed!
            return t

        if total_rate <= 0.0:
            # No more failures possible => infinite lifetime
            return np.inf

        # Sample time to next failure
        dt = np.random.exponential(1.0 / total_rate)
        t += dt

        # Sample which component fails from fenwick tree
        r = np.random.random() * total_rate
        idx = bit_find_index(bit, r)

        # Apply failure
        if idx < n_edges:
            # Edge fails
            edge_state[idx] = 0
            # Remove from Fenwick Tree (set rate to 0)
            old_rate = lam_edges_arr[idx]
            bit_update(bit, idx, -old_rate)
            total_rate -= old_rate
        else:
            # Node fails
            ni = idx - n_edges
            node_state[ni] = 0
            # Remove from Fenwick Tree
            old_rate = lam_nodes_arr[ni]
            bit_update(bit, idx, -old_rate)
            total_rate -= old_rate