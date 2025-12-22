import networkx as nx
import random
import statistics
import numpy as np
import matplotlib.pyplot as plt

# try importing Numba
try:
    from numba import njit, prange

    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    print("Warning: Numba not available. Using Python-only version.")

# ----------------------------------------------------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------------------------------------------------

def get_lam_mu_from_graph(G):
    """Extract failure and repair rates from graph attributes"""
    lam_edges, mu_edges = {}, {}
    lam_nodes, mu_nodes = {}, {}

    for e in G.edges(data=True):
        u, v, edata = e
        mtbf_h = edata.get('mtbf_h', 0)
        lam = 0 if mtbf_h == 0 else 1 / mtbf_h
        lam_edges[(u, v)] = lam

        mttr_h = edata.get('mttr_h', 0)
        mu = 0 if mttr_h == 0 else 1 / mttr_h
        mu_edges[(u, v)] = mu

        #print(f"mtbf_h={mtbf_h}, lam={lam},\n mttr_h={mttr_h}, mu={mu}")

    for n in G.nodes(data=True):
        u, ndata = n
        mtbf_h = ndata.get('mtbf_h', 0)
        lam = 0 if mtbf_h == 0 else 1 / mtbf_h
        lam_nodes[u] = lam

        mttr_h = ndata.get('mttr_h', 0)
        mu = 0 if mttr_h == 0 else 1 / mttr_h
        mu_nodes[u] = mu

    return lam_edges, lam_nodes, mu_edges, mu_nodes


def calc_max_time(lam_edges, lam_nodes, mu_edges, mu_nodes):
    '''
    DEPRECATED: replaced by event based timeout (max_events).
    Calculates upper bound for MTTF (see doc)

    :INPUT:
        **lam_edges**   - dict, failure rates for edges
        **lam_nodes**   - dict, failure rates for nodes
        **mu_edges**    - dict, repair rates for edges
        **mu_nodes**    - dict, repair rates for nodes

    :OUTPUT:
        **max_time**   - float, upper bound for MTTF
    '''
    # init A_max and MTTR_max
    A_max, MTTR_max = 1.0, 0.0
    # iterate over edges
    for lam, mu in zip(lam_edges.values(), mu_edges.values()):
        MTTF, MTTR = 1 / lam, 1 / mu
        MTTR_max += MTTR
        A_i = MTTF / (MTTF + MTTR)
        A_max *= (1 - A_i)

    # iterate over nodes
    for lam, mu in zip(lam_nodes.values(), mu_nodes.values()):
        MTTF, MTTR = 1 / lam, 1 / mu
        MTTR_max += MTTR
        A_i = MTTF / (MTTF + MTTR)
        A_max *= (1 - A_i)

    A_max = 1 - A_max
    if A_max != 1:
        max_time = A_max / (1 - A_max) * MTTR_max
        return max_time
    print('Availability equals one leading to division by zero. Using fallback.')
    return 1e8


def graph_to_numba_arrays(G, source, target):
    """
    Convert NetworkX graph to Numba-compatible np.ndarrays

    :INPUT:
        **G**      - networkx.Graph, topology of network
        **source** - string, classifying source node
        **target** - string, classifying target node

    :OUTPUT:
        {
        **n_nodes**     - int, number of nodes
        **n_edges**     - int, number of edges
        **adj_offsets** - np.ndarray,
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

    # Node index mapping
    node_to_idx = {n: i for i, n in enumerate(node_list)}
    source_idx = node_to_idx[source]
    target_idx = node_to_idx[target]

    # Edge arrays
    edge_u = np.empty(n_edges, dtype=np.int64)
    edge_v = np.empty(n_edges, dtype=np.int64)
    for i, (u, v) in enumerate(edge_list):
        edge_u[i] = node_to_idx[u]
        edge_v[i] = node_to_idx[v]

    # Build CSR adjacency structure
    deg = np.zeros(n_nodes, dtype=np.int64)
    for u_i, v_i in zip(edge_u, edge_v):
        deg[u_i] += 1
        deg[v_i] += 1

    adj_offsets = np.empty(n_nodes + 1, dtype=np.int64)
    adj_offsets[0] = 0
    for i in range(n_nodes):
        adj_offsets[i + 1] = adj_offsets[i] + deg[i]

    total_adj = adj_offsets[n_nodes]
    adj_nodes = np.empty(total_adj, dtype=np.int64)
    adj_edges = np.empty(total_adj, dtype=np.int64)

    # Fill adjacency arrays
    cur = np.zeros(n_nodes, dtype=np.int64)
    for ei, (u_i, v_i) in enumerate(zip(edge_u, edge_v)):
        # Add edge u→v
        pos_u = adj_offsets[u_i] + cur[u_i]
        adj_nodes[pos_u] = v_i
        adj_edges[pos_u] = ei
        cur[u_i] += 1

        # Add edge v→u
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
        'source_idx': source_idx,
        'target_idx': target_idx,
        'edge_list': edge_list,
        'node_list': node_list
    }


# ======================================================================================================================
# NUMBA VERSION (Fenwick Tree + DFS)
# ======================================================================================================================
if NUMBA_AVAILABLE:

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
    def _build_rates_and_bit(n_edges, n_nodes, lam_edges_arr, lam_nodes_arr,
                             mu_edges_arr=None, mu_nodes_arr=None, repairable=True):
        """Build rates array and Fenwick Tree."""
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
    # DFS Connectivity Check (replacing networkX.has_path)
    # ------------------------------------------------------------------------------------------------------------------
    @njit
    def dfs_connected(adj_offsets, adj_nodes, adj_edges, edge_state, node_state,
                      source_idx, target_idx):
        """
        Depth First Search to determine connectivity of network (replaces slow NetworkX method)
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
                            source_idx, target_idx,
                            lam_edges_arr, lam_nodes_arr,
                            mu_edges_arr, mu_nodes_arr, bit,
                            depth, max_events=-1, laziness=0, track_crit=True):
        """
        Core simulation loop in Numba which simulates UP->DOWN - cycles for depth deep.
        Returns array of (t_fail, t_repair) for each cycle.
        :INPUT:
            **n_edges, n_nodes**                    - ints, number of edges and nodes in network
            **adj_offsets, adj_nodes, adj_edges**   - np.ndarrays, topology of graph in csr format
            **source_idx, target_idx**              - integers, indices of source and target nodes
            **lam_edges_arr, lam_nodes_arr**        - np.ndarrays, failure rates of edges and nodes
            **mu_edges_arr, mu_nodes_arr**          - np.ndarrays, repair rates of edges and nodes
            **bit**                                 - Fenwick Tree Array, containing initial rates
            **depth**                               - int, number of cycles to be simulated on the semi-fixed network
            **max_events**                            - float, maximum simulation time, to avoid infinite loops
            **laziness**                            - float, between 0 and 1. Percentage by which the network has to
                                                      change before connectivity is checked again.
        :OUTPUT:
            **results**                             - list of (t_fail, t_repair) for each cycle
        """

        # Initialize states (all UP)
        edge_state = np.ones(n_edges, dtype=np.bool_)
        node_state = np.ones(n_nodes, dtype=np.bool_)

        # get total number of possible events
        n_events = n_edges + n_nodes

        if max_events == -1:
            max_events = n_events * 50 # stop loop if the whole network has changed 50 times

        total_rate = bit_prefix_sum(bit, n_events - 1)

        # Results storage
        results = np.empty((depth, 2), dtype=np.float64)
        cycle_idx = 0

        if laziness < 0:
            print('Choose Values in [0,1) for Laziness')
            laziness=0

        # threshold after which connectivity is checked again
        event_threshold = int(laziness * n_events)

        if track_crit:
            # preallocate array for the identification of critical components. (-1 = invalid)
            critical_components = np.full(2 * (event_threshold+1) * depth, -1, dtype=np.int32)
        else:
            critical_components = np.empty(0, dtype=np.int32)

        crit_idx = 0
        crit_checkpoint = 0  # position on last successful check

        # Main cycle loop
        while cycle_idx < depth:

            # === PHASE 1: UP → DOWN (run until failure) ===
            t_fail = 0.0
            connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                      edge_state, node_state, source_idx, target_idx)

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
                    print('\nmax_events reached: System didnt fail and is likely stuck in its current state.\n'
                          'That means the system is very robust and will most likely never fail!')
                    results[cycle_idx, 0] = np.inf
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
                event_count+=1
                event_idx+=1

                # store last event
                if track_crit:
                    critical_components[crit_idx] = idx
                    crit_idx += 1

                # Lazy connectivity check
                if event_count >= event_threshold:
                    connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                              edge_state, node_state, source_idx, target_idx)
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

            connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                      edge_state, node_state, source_idx, target_idx)

            while not connected:
                if total_rate <= 0.0:
                    return results[:cycle_idx], critical_components[:crit_idx]

                dt = np.random.exponential(1.0 / total_rate)
                t_repair += dt
                if event_idx >= max_events:
                    print('max_events reached: System couldnt be repaired and is likely stuck in its current state.\n'
                          'That means the system isnt very robust and will most likely never be restored!')
                    results[cycle_idx, 1] = np.inf
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
                event_count+=1
                event_idx+=1

                if event_count >= event_threshold:
                    connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                              edge_state, node_state, source_idx, target_idx)
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
                                     source_idx, target_idx,
                                     lam_edges_arr, lam_nodes_arr, bit):
        """
        Simulate system lifetime for a non-repairable system (µ=0).
        :INPUT:
            **n_edges, n_nodes**                    - ints, number of edges and nodes in network
            **adj_offsets, adj_nodes, adj_edges**   - np.ndarrays, topology of graph in csr format
            **source_idx, target_idx**              - integers, indices of source and target nodes
            **lam_edges_arr, lam_nodes_arr**        - np.ndarrays, failure rates of edges and nodes

        :OUTPUT:
            **t** - float, time until first system failure (MTTF sample)
        """

        # TODO: edge_state, node_state, n_events, rates, bit, total_rate is static and can hence be prebuild.
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
            connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                      edge_state, node_state, source_idx, target_idx)

            if not connected:
                # System failed!
                return t

            if total_rate <= 0.0:
                # No more failures possible → infinite lifetime
                return np.inf

            # Sample time to next failure
            dt = np.random.exponential(1.0 / total_rate)
            t += dt

            # Sample which component fails (Fenwick Tree!)
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


    # ------------------------------------------------------------------------------------------------------------------
    # Wrappers for parallel and serial code execution
    # ------------------------------------------------------------------------------------------------------------------
    @njit(parallel=True)
    def _run_parallel(n_sims,
                      n_edges, n_nodes,
                      adj_offsets, adj_nodes, adj_edges,
                      source_idx, target_idx,
                      lam_edges_arr, lam_nodes_arr,
                      mu_edges_arr, mu_nodes_arr,
                      depth, max_events, laziness=0, analyze_crit=True):
        """
        Run n_sims in parallel.
        Uses all N CPU-Cores to each run n_sims/N simulation simulations
        Speedup: ~Nx with N Cores.
        """
        all_results = np.empty((n_sims, 2), dtype=np.float64)

        # Build event list
        n_events = n_edges + n_nodes
        rates = np.empty(n_events, dtype=np.float64)

        # prebuild list of rates
        for i in range(n_edges):
            rates[i] = lam_edges_arr[i]
        for j in range(n_nodes):
            rates[n_edges + j] = lam_nodes_arr[j]

        # prebuild fenwick tree
        bit = bit_build_from_array(rates)

        # threshold to check connectivity
        event_threshold = int(laziness * n_events)

        # calc max events per simulation to store critical components
        max_crit_per_sim = 2 * (event_threshold + 1) * depth

        if analyze_crit:
            # preallocate array for critical components
            all_critical = np.full((n_sims, max_crit_per_sim), -1, dtype=np.int32)
        else:
            all_critical = np.empty((0,0), dtype=np.int32)

        # core parallelisation routine
        for sim_idx in prange(n_sims):
            bit_copy = bit.copy()

            results, crit_comp = simulate_numba_core(
                n_edges, n_nodes,
                adj_offsets, adj_nodes, adj_edges,
                source_idx, target_idx,
                lam_edges_arr, lam_nodes_arr,
                mu_edges_arr, mu_nodes_arr, bit_copy,
                depth, max_events, laziness, track_crit=analyze_crit
            )

            if results.shape[0] > 0:
                all_results[sim_idx, 0] = float(np.mean(results[:,0]))
                all_results[sim_idx, 1] = float(np.mean(results[:,1]))

                if analyze_crit:
                    n_crit = min(crit_comp.shape[0], max_crit_per_sim)
                    all_critical[sim_idx, :n_crit] = crit_comp[:n_crit]
            else:
                # Markiere als invalid
                all_results[sim_idx, :] = np.nan

        return all_results, all_critical


    @njit(parallel=True)
    def _run_parallel_norepair(n_sims,
                               n_edges, n_nodes,
                               adj_offsets, adj_nodes, adj_edges,
                               source_idx, target_idx,
                               lam_edges_arr, lam_nodes_arr):
        """
        Run n_sims in parallel.
        Uses all N CPU-Cores to each run n_sims/N simulation runs
        Speedup: ~Nx with N Cores.
        """
        all_results = np.empty(n_sims, dtype=np.float64)

        bit_template = _build_rates_and_bit(n_edges, n_nodes,
                                            lam_edges_arr, lam_nodes_arr,
                                            repairable=False)

        # core parallelisation routine
        for sim_idx in prange(n_sims):
            bit_copy = bit_template.copy()
            results = simulate_numba_core_norepair(
                n_edges, n_nodes,
                adj_offsets, adj_nodes, adj_edges,
                source_idx, target_idx,
                lam_edges_arr, lam_nodes_arr, bit_copy
            )

            all_results[sim_idx] = results

        return all_results


    @njit
    def _run_serial(n_sims, n_edges, n_nodes,
                    adj_offsets, adj_nodes, adj_edges,
                    source_idx, target_idx,
                    lam_edges_arr, lam_nodes_arr,
                    mu_edges_arr, mu_nodes_arr,
                    depth, max_events,
                    laziness=0, track_crit=True):
        """
        Wrapper to run n_sims repairable simulations serially.
        Same structure as parallel, but with range instead of prange.
        """
        all_results = np.empty((n_sims, 2), dtype=np.float64)
        n_events = n_edges + n_nodes

        # Prebuild Fenwick Tree
        bit_template = _build_rates_and_bit(n_edges, n_nodes,
                                            lam_edges_arr, lam_nodes_arr,
                                            mu_edges_arr, mu_nodes_arr)

        # Critical components storage
        event_threshold = int(laziness * n_events)

        max_crit_per_sim = 2 * (event_threshold + 1) * depth

        if track_crit:
            all_critical = np.full((n_sims, max_crit_per_sim), -1, dtype=np.int32)
        else:
            all_critical = np.empty((0, 0), dtype=np.int32)

        # Serial loop
        for sim_idx in range(n_sims):
            bit_copy = bit_template.copy()

            results, crit_comp = simulate_numba_core(
                n_edges, n_nodes,
                adj_offsets, adj_nodes, adj_edges,
                source_idx, target_idx,
                lam_edges_arr, lam_nodes_arr,
                mu_edges_arr, mu_nodes_arr,
                bit_copy,
                depth, max_events, laziness, track_crit
            )

            if results.shape[0] > 0:
                all_results[sim_idx, 0] = np.mean(results[:, 0])
                all_results[sim_idx, 1] = np.mean(results[:, 1])

                if track_crit:
                    n_crit = min(crit_comp.shape[0], max_crit_per_sim)
                    all_critical[sim_idx, :n_crit] = crit_comp[:n_crit]
            else:
                all_results[sim_idx, :] = np.nan

        return all_results, all_critical


    @njit
    def _run_serial_norepair(n_sims, n_edges, n_nodes,
                             adj_offsets, adj_nodes, adj_edges,
                             source_idx, target_idx,
                             lam_edges_arr, lam_nodes_arr):
        """Wrapper for running n_sims non-repairable simulations serially."""
        all_results = np.empty(n_sims, dtype=np.float64)

        bit_template = _build_rates_and_bit(n_edges, n_nodes,
                                            lam_edges_arr, lam_nodes_arr,
                                            repairable=False)

        for sim_idx in range(n_sims):
            bit_copy = bit_template.copy()

            result = simulate_numba_core_norepair(
                n_edges, n_nodes,
                adj_offsets, adj_nodes, adj_edges,
                source_idx, target_idx,
                lam_edges_arr, lam_nodes_arr,
                bit_copy
            )
            all_results[sim_idx] = result

        return all_results


# =====================================================================================
# PYTHON-ONLY Fallback (Union-Find)
# =====================================================================================
class UnionFind:
    """Optimized Union-Find structure for connectivity checks (replaces networkX)"""

    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        self.rank = {n: 0 for n in nodes}

    def find(self, x):
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        root_x, root_y = self.find(x), self.find(y)
        # check if already unified
        if root_x == root_y:
            return
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1

    def connected(self, x, y):
        return self.find(x) == self.find(y)

    def rebuild_uf(self, edge_list, node_list, edge_state, node_state, node_index):
        """Rebuild Union-Find structure from scratch"""
        for n in node_list:
            self.parent[n] = n
            self.rank[n] = 0
        for i, (u, v) in enumerate(edge_list):
            # two nodes are connected if they are both UP and their related edge is UP
            if edge_state[i] and node_state[node_index[u]] and node_state[node_index[v]]:
                self.union(u, v)


def _simulate_python_repairable(G, source, target,
                                lam_edges, lam_nodes,
                                mu_edges, mu_nodes,
                                depth=1, max_events=-1):
    """
    Python version with Union-Find (original implementation).
    """
    edge_list = list(G.edges())
    node_list = list(G.nodes())

    # Initialize states (all UP)
    edge_state = [1] * len(edge_list)
    node_state = [1] * len(node_list)

    edge_index = {e: i for i, e in enumerate(edge_list)}
    node_index = {n: i for i, n in enumerate(node_list)}

    if max_events == -1:
        n_events = len(edge_list) + len(node_list)
        max_events = n_events * 50

    events = []
    for i, e in enumerate(edge_list):
        events.append(("edge", i, lam_edges[e], mu_edges[e]))
    for i, n in enumerate(node_list):
        events.append(("node", i, lam_nodes[n], mu_nodes[n]))

    total_rate = sum(lam_edges[e] for e in edge_list) + sum(lam_nodes[n] for n in node_list)

    uf = UnionFind(node_list)
    uf.rebuild_uf(edge_list, node_list, edge_state, node_state, node_index)

    needs_rebuild = False

    results = []
    for _ in range(depth):

        # === PHASE 1: UP → DOWN (run until failure) ===
        t = 0.0
        event_idx = 0

        while True:
            if needs_rebuild:
                uf.rebuild_uf(edge_list, node_list, edge_state, node_state, node_index)
                needs_rebuild = False

            is_connected = uf.connected(source, target)
            if not is_connected:
                break

            if total_rate == 0:
                print("lambda, mu are all 0. Please define rates.")
                return None

            dt = random.expovariate(total_rate)
            t += dt
            if event_idx >= max_events:
                print('System stuck in cycle. Doesnt fail!')
                return None
            event_idx += 1

            # Linear search with early exit
            r = random.random() * total_rate
            cum = 0.0
            for etype, idx, lam, mu in events:
                if etype == "edge":
                    rate = lam if edge_state[idx] else mu
                else:
                    rate = lam if node_state[idx] else mu

                cum += rate
                if cum >= r:
                    if etype == "edge":
                        old = edge_state[idx]
                        edge_state[idx] = 1 - old
                        total_rate += (mu - lam) if old else (lam - mu)
                    else:
                        old = node_state[idx]
                        node_state[idx] = 1 - old
                        total_rate += (mu - lam) if old else (lam - mu)
                    needs_rebuild = True
                    break

        t_fail = t
        if t_fail is None:
            return None

        t = 0.0
        event_idx = 0
        while True:
            if needs_rebuild:
                uf.rebuild_uf(edge_list, node_list, edge_state, node_state, node_index)
                needs_rebuild = False

            is_connected = uf.connected(source, target)
            if is_connected:
                break

            if total_rate == 0:
                return None

            dt = random.expovariate(total_rate)
            t += dt
            if event_idx >= max_events:
                print('System stuck in repair cycle. Couldnt be repaired!')
                return None

            event_idx += 1

            # Linear search with early exit
            r = random.random() * total_rate
            cum = 0.0
            for etype, idx, lam, mu in events:
                if etype == "edge":
                    rate = lam if edge_state[idx] else mu
                else:
                    rate = lam if node_state[idx] else mu

                cum += rate
                if cum >= r:
                    if etype == "edge":
                        old = edge_state[idx]
                        edge_state[idx] = 1 - old
                        total_rate += (mu - lam) if old else (lam - mu)
                    else:
                        old = node_state[idx]
                        node_state[idx] = 1 - old
                        total_rate += (mu - lam) if old else (lam - mu)
                    needs_rebuild = True
                    break

        t_repair = t

        if t_repair is None:
            return None
        results.append((t_fail, t_repair))

    if not results:
        return None

    mttf = statistics.mean(r[0] for r in results)
    mttr = statistics.mean(r[1] for r in results)
    return mttf, mttr


def _simulate_python_norepair(G, source, target, lam_edges, lam_nodes):
    """Non-repairable system simulation (unchanged)"""
    edge_list = list(G.edges())
    node_list = list(G.nodes())
    node_index = {n: i for i, n in enumerate(node_list)}

    edge_state = [1] * len(edge_list)
    node_state = [1] * len(node_list)

    active_events = []
    for i, e in enumerate(edge_list):
        active_events.append(("edge", i, lam_edges[e]))
    for i, n in enumerate(node_list):
        active_events.append(("node", i, lam_nodes[n]))

    total_rate = sum(rate for _, _, rate in active_events)

    uf = UnionFind(node_list)
    uf.rebuild_uf(edge_list, node_list, edge_state, node_state, node_index)

    t = 0.0

    while uf.connected(source, target):
        if total_rate == 0:
            return np.inf

        dt = random.expovariate(total_rate)
        t += dt

        r = random.random() * total_rate
        cum = 0.0

        for event_idx, (etype, idx, rate) in enumerate(active_events):
            cum += rate
            if cum >= r:
                if etype == "edge":
                    edge_state[idx] = 0
                else:
                    node_state[idx] = 0

                total_rate -= rate
                active_events.pop(event_idx)
                uf.rebuild_uf(edge_list, node_list, edge_state, node_state, node_index)
                break

    return t


# ----------------------------------------------------------------------------------------------------------------------
# Critical Component Analysis
# ----------------------------------------------------------------------------------------------------------------------
def analyze_critical_components(all_critical, n_edges, n_nodes,
                                edge_list, node_list,
                                lam_edges_arr, lam_nodes_arr,
                                mu_edges_arr, mu_nodes_arr,
                                top_n=5, plot=True, verbose=True, rate_adjustment=True):
    """
    TODO: validate function
    TODO: output a plot which shows the topology and colors the critical components in red
    Analyze which components are disproportionately critical by calculating the expected
    :INPUT:
        **all_critical**    -
        **n_edges**         -
        **n_nodes**         -
        **edge_list**       -
        **node_list**       -
        **lam_edges_arr**   -
        **lam_nodes_arr**   -
        **mu_edges_arr**    -
        **mu_nodes_arr**    -
        **top_n**           -
        **plot**            -
        **verbose**         -
        **rate_adjustment** - Boolean, choose whether to adjust the counts by their rates.
                              This determines whether the network is analyzed for bare topological
                              criticalities (True) or a wholistic analysis of critical components
                              is performed, which explicitly depends on the rates of the components (False).

    :OUTPUT:
        dict with edge_criticality, node_criticality, counts, plots, etc.

    """
    if top_n == 0:
        top_n = -1

    n_events = n_edges + n_nodes

    # Flatten and filter invalid values (-1)
    flat = all_critical.flatten()
    valid = flat[flat >= 0]

    if len(valid) == 0:
        print("No critical components tracked!")
        return None

    # Count occurrences
    unique_idx, counts = np.unique(valid, return_counts=True)

    # build array of counts (zero for components that never occured)
    full_counts = np.zeros(n_events, dtype=np.float64)
    for idx, count in zip(unique_idx, counts):
        if idx < n_events:
            full_counts[idx] = count

    # Normalize by expected rates (λ + μ)
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
            elif not rate_adjustment: # skip expected_fraction <= 0
                criticality[i] = (full_counts[i] / total_observed)

    edge_crit = criticality[:n_edges]
    node_crit = criticality[n_edges:]

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
        print("  ≈ 1.0: As expected")
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


def monte_carlo_plotting(mttf, mttr=None, bins="auto",
                         rng=None, density=True, weights=None,
                         show_errors=True, color="C0", label=None,
                         ax=None, gaussian=True, gaussian_color="C3", gaussian_label="Gauss-Fit",
                         title="Monte-Carlo Histogram (MTTF)"):

    '''Bar chart of samples'''
    samples = np.asarray(mttf)

    # Achse/Figur
    created_ax = False
    if ax is None:
        fig, ax = plt.subplots()
        created_ax = True
    else:
        fig = ax.figure

    # Bin-Kanten
    edges = np.histogram_bin_edges(samples, bins=bins, range=rng)
    widths = np.diff(edges)
    centers = edges[:-1] + 0.5 * widths

    # Summen je Bin (mit Gewichten)
    sumw, _ = np.histogram(samples, bins=edges, weights=weights)
    if weights is None:
        # Poisson-Varianz
        var = sumw
    else:
        sumw2, _ = np.histogram(samples, bins=edges, weights=np.square(weights))
        var = sumw2

    if density:
        total = sumw.sum()
        # Dichtehöhe pro Bin: p_i / (total * binbreite)
        heights = np.divide(sumw, total * widths, out=np.zeros_like(sumw, dtype=float), where=widths > 0)
        # Fehlerfortpflanzung (Näherung, vernachlässigt Korrelation mit total):
        errors = np.divide(np.sqrt(var), total * widths, out=np.zeros_like(var, dtype=float), where=widths > 0)
        y_label = "Dichte"
    else:
        heights = sumw
        errors = np.sqrt(var)
        y_label = "Count"

    # Plot
    ax.bar(centers, heights, align="center", width=widths, color=color, alpha=0.7, edgecolor="black", label=label)
    if show_errors:
        ax.errorbar(centers, heights, yerr=errors, fmt="none", ecolor="black", capsize=2, lw=1)

    fit_out = {}
    if gaussian:

        try:
            from scipy.optimize import curve_fit
            from scipy.special import erf
        except ImportError as e:
            raise ImportError("Für den Gauß-Fit wird scipy benötigt: pip install scipy") from e

        # Gaußsche Dichte
        def gauss_pdf(x, mu, sigma):
            sigma = np.abs(sigma)
            return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (np.sqrt(2 * np.pi) * sigma)

        # CDF der Gaußverteilung (für Bin-Integrale)
        def gauss_cdf(x, mu, sigma):
            sigma = np.abs(sigma)
            return 0.5 * (1.0 + erf((x - mu) / (np.sqrt(2) * sigma)))

        # Fit-Daten (maskierte Bins)
        mask = (widths > 0) & np.isfinite(heights) & np.isfinite(errors) & (errors > 0)
        xfit = centers[mask]
        yfit = heights[mask]
        efit = errors[mask]

        # Startwerte
        mu0 = float(np.mean(samples))
        sigma0 = float(np.std(samples, ddof=1)) if samples.size > 1 else 1.0
        if not np.isfinite(sigma0) or sigma0 <= 0:
            sigma0 = 1.0
        A0 = float(np.sum(yfit * (widths[mask] if not density else 1.0))) if not density else 1.0

        if xfit.size >= 3:
            # Modell: Dichte vs. Zählungen
            if density:
                # y_i ≈ A * pdf(center_i)
                def model(x, A, mu, sigma):
                    return A * gauss_pdf(x, mu, sigma)
            else:
                # y_i ≈ A * ∫_{edge_lo}^{edge_hi} pdf dx = A * (CDF(hi) - CDF(lo))
                elo = edges[:-1][mask]
                ehi = edges[1:][mask]

                def model(x, A, mu, sigma):
                    return A * (gauss_cdf(ehi, mu, sigma) - gauss_cdf(elo, mu, sigma))

            p0 = (A0, mu0, sigma0)
            bounds = ((0.0, -np.inf, 1e-12), (np.inf, np.inf, np.inf))
            popt, pcov = curve_fit(model, xfit, yfit, p0=p0, sigma=efit, absolute_sigma=True,
                                   bounds=bounds, maxfev=10000)
            A_hat, mu_hat, sigma_hat = popt

            # Chi^2 / ndf
            chi2 = float(np.sum(((yfit - model(xfit, *popt)) / efit) ** 2))
            ndf = int(xfit.size - len(popt)) if xfit.size > len(popt) else 0

            fit_out = {"fit_params": (A_hat, mu_hat, sigma_hat), "fit_cov": pcov,
                       "chi2": chi2, "ndf": ndf}

            # Plot der Fit-Kurve
            if density:
                xs = np.linspace(edges[0], edges[-1], 600)
                ys = A_hat * gauss_pdf(xs, mu_hat, sigma_hat)
                lbl = f"Gauss-Fit: μ={mu_hat:.3g}, σ={sigma_hat:.3g}, A={A_hat:.3g}"
                if ndf > 0:
                    lbl += f", χ²/ndf={chi2 / ndf:.2f}"
                ax.plot(xs, ys, color=gaussian_color, lw=2, label=lbl)
            else:
                # Erwartete Zählungen pro Bin (über alle Bins, unmaskiert)
                ybins = A_hat * (gauss_cdf(edges[1:], mu_hat, sigma_hat) - gauss_cdf(edges[:-1], mu_hat, sigma_hat))
                xs = np.repeat(edges, 2)[1:-1]
                ys = np.repeat(ybins, 2)
                lbl = f"Gauss-Fit: μ={mu_hat:.3g}, σ={sigma_hat:.3g}, A={A_hat:.3g}"
                if ndf > 0:
                    lbl += f", χ²/ndf={chi2 / ndf:.2f}"
                ax.plot(xs, ys, color=gaussian_color, lw=2, label=lbl)
        else:
            print("Warnung: Zu wenige valide Bins für einen stabilen Gauß-Fit.")
    ax.set_xlabel("Value")
    ax.set_ylabel(y_label)
    ax.set_title(title)
    if label:
        ax.legend()

    result = {
        "edges": edges,
        "centers": centers,
        "heights": heights,
        "errors": errors
    }
    fig2, ax2, res2 = None, None, None
    if mttr is not None:
        fig2, ax2, res2 = monte_carlo_plotting(mttf=mttr, title="Monte-Carlo Histogramm (MTTR)")

    plt.show()
    return fig, ax, result


# ----------------------------------------------------------------------------------------------------------------------
# run N Monte Carlo simulations and estimate reliability metrics from samples
# ----------------------------------------------------------------------------------------------------------------------
def estimate_mttf_mttr(G, source, target, N=1000, depth=1,
                       use_numba=True, parallel=True, plotting=False,
                       laziness=0, analyze_crit=False):
    """
    Run N Monte Carlo simulations and estimate MTTF/MTTR.

    :INPUT:
        **G**           - NetworkX graph with 'mtbf_h' and 'mttr_h' attributes on nodes and edges.
        **source**      - Source node
        **target**      - Target node
        **N**:          - Number of simulations
        **depth**       - Number of UP/DOWN cycles per simulation run (only repairable).
                          Adjusts for the natural bias towards larger reliabilities when starting each new cycle
                          with a fully functional network. Depth hands over a semi-fixed network.
                          ~200 gives reasonable values.
        **use_numba**   - Boolean, use Numba-optimized version if available (default: True)
        **plotting**    - Boolean, enable plotting displaying the distribution of values
        **parallel**    - Boolean, enable parallelization (default: True)
        **laziness**    - float in [0,1), parameter which allows to sacrifice some accuracy for performance.
                          Only checks the connectivity of the network if Lazyness*(V+E) events took place

    Returns:
        (mttf, mttr): Mean time to failure and mean time to repair
    """
    # Catch if G is not connected at start.
    if not nx.has_path(G, source, target):
        print('There exists no connection between source and target. Please fix topology!')
        return None, None

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
        return np.inf, 0.0

    if use_numba and NUMBA_AVAILABLE:
        # Convert to arrays
        conv = graph_to_numba_arrays(G, source, target)

        # get edge and node arrays
        lam_edges_arr = np.array([lam_edges[e] for e in conv['edge_list']], dtype=np.float64)
        lam_nodes_arr = np.array([lam_nodes[n] for n in conv['node_list']], dtype=np.float64)

        if is_nonrepairable:
            # non-repairable case
            if parallel:
                print(f"Running {N} simulations in parallel...")
                all_results = _run_parallel_norepair(
                    N, conv['n_edges'], conv['n_nodes'],
                    conv['adj_offsets'], conv['adj_nodes'],
                    conv['adj_edges'], conv['source_idx'],
                    conv['target_idx'], lam_edges_arr,
                    lam_nodes_arr
                )
            else:
                all_results = _run_serial_norepair(
                    N, conv['n_edges'], conv['n_nodes'],
                    conv['adj_offsets'], conv['adj_nodes'],
                    conv['adj_edges'], conv['source_idx'],
                    conv['target_idx'], lam_edges_arr,
                    lam_nodes_arr
                )
            # Filter valid results
            valid = all_results[~np.isnan(all_results)]

            if len(valid) == 0:
                return None, None

            return float(np.mean(valid)), np.inf

        else:
            # Repairable case
            mu_edges_arr = np.array([mu_edges[e] for e in conv['edge_list']], dtype=np.float64)
            mu_nodes_arr = np.array([mu_nodes[n] for n in conv['node_list']], dtype=np.float64)

            max_events=-1

            print(f"Running {N*depth} ({N} x {depth}) simulations {'in parallel' if parallel else ''}...")

            if parallel:
                all_results, all_critical = _run_parallel(
                    N,
                    conv['n_edges'], conv['n_nodes'],
                    conv['adj_offsets'], conv['adj_nodes'], conv['adj_edges'],
                    conv['source_idx'], conv['target_idx'],
                    lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr,
                    depth, max_events, laziness, analyze_crit
                )
            else:
                all_results, all_critical = _run_serial(
                    N,
                    conv['n_edges'], conv['n_nodes'],
                    conv['adj_offsets'], conv['adj_nodes'], conv['adj_edges'],
                    conv['source_idx'], conv['target_idx'],
                    lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr,
                    depth, max_events, laziness, analyze_crit
                )
            valid = ~np.isnan(all_results[:,0])
            mttf_samples = all_results[valid, 0]
            mttr_samples = all_results[valid, 1]

            if len(mttf_samples) == 0:
                return None, None

            if analyze_crit and all_critical.size >0:
                analyze_critical_components(
                    all_critical, conv['n_edges'], conv['n_nodes'],
                    conv['edge_list'], conv['node_list'],
                    lam_edges_arr, lam_nodes_arr,
                    mu_edges_arr, mu_nodes_arr, plot=True
                )

            if plotting:
                monte_carlo_plotting(mttf_samples, mttr_samples)

            return float(np.mean(mttf_samples)), float(np.mean(mttr_samples))

    # Python fallback
    print(f"Using Python fallback ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

    if is_nonrepairable:
        samples = [_simulate_python_norepair(G, source, target, lam_edges, lam_nodes) for _ in range(N)]
        return float(np.mean(samples)), np.inf
    else:
        #max_events = calc_max_time(lam_edges, lam_nodes, mu_edges, mu_nodes)
        results = []
        for _ in range(N):
            res = _simulate_python_repairable(G, source, target, lam_edges, lam_nodes,
                                                  mu_edges, mu_nodes, depth)
            if res is not None:
                results.append(res)

        if not results:
            return None, None

        mttf_samples = [r[0] for r in results]
        mttr_samples = [r[1] for r in results]


        if plotting:
            monte_carlo_plotting(mttf_samples, mttr_samples)

        return float(np.mean(mttf_samples)), float(np.mean(mttr_samples))
