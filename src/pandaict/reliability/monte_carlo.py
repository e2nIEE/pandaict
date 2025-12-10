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
# UNION-FIND structure (fallback if numba not available
# ----------------------------------------------------------------------------------------------------------------------
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
                            mu_edges_arr, mu_nodes_arr,
                            max_cycles, max_time, Laziness=0):
        """
        Core simulation loop in Numba which simulates UP->DOWN - cycles for max_cycles deep.
        Returns array of (t_fail, t_repair) for each cycle.
        :INPUT:
            **n_edges, n_nodes**                    - ints, number of edges and nodes in network
            **adj_offsets, adj_nodes, adj_edges**   - np.ndarrays, topology of graph in csr format
            **source_idx, target_idx**              - integers, indices of source and target nodes
            **lam_edges_arr, lam_nodes_arr**        - np.ndarrays, failure rates of edges and nodes
            **mu_edges_arr, mu_nodes_arr**          - np.ndarrays, repair rates of edges and nodes
            **max_cycles**                          - int, number of cycles to be simulated on the semi-fixed network
            **max_time**                            - float, maximum simulation time, to avoid infinite loops
            **Laziness**                            - float, between 0 and 1. Percentage by which the network has to
                                                      change before connectivity is checked again.

        :OUTPUT:
            **results**                             - list of (t_fail, t_repair) for each cycle
        """

        # Initialize states (all UP)
        edge_state = np.ones(n_edges, dtype=np.bool)
        node_state = np.ones(n_nodes, dtype=np.bool)

        # get total number of possible events
        n_events = n_edges + n_nodes

        # Initial rates (all UP)
        rates = np.empty(n_events, dtype=np.float64)

        # Build array of rates (edges first, nodes second)
        for i in range(n_edges):
            rates[i] = lam_edges_arr[i]
        for j in range(n_nodes):
            rates[n_edges + j] = lam_nodes_arr[j]

        # Build Fenwick Tree for efficient sampling
        bit = bit_build_from_array(rates)
        total_rate = bit_prefix_sum(bit, n_events - 1)

        # Results storage
        results = np.empty((max_cycles, 2), dtype=np.float64)
        cycle_idx = 0

        # Main cycle loop
        while cycle_idx < max_cycles:

            # === PHASE 1: UP → DOWN (run until failure) ===
            t_fail = 0.0
            connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                      edge_state, node_state, source_idx, target_idx)

            # keep track of event number
            event_idx = 1
            event_count = -1

            while connected:
                if total_rate <= 0.0:
                    return np.empty((0, 2), dtype=np.float64)  # failure

                # Sample time to next event
                dt = np.random.exponential(1.0 / total_rate)
                t_fail += dt
                if t_fail > max_time:
                    print('max_time reached! System didnt fail in time.')
                    return np.empty((0, 2), dtype=np.float64)

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

                event_count += 1
                # Check connectivity only if a certain portion of the network has changed
                if event_count == int(Laziness*n_events):
                    # reset event_count
                    event_count = -1
                    connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                              edge_state, node_state, source_idx, target_idx)
                event_idx += 1

            # === PHASE 2: DOWN → UP (run until repair) ===
            t_repair = 0.0
            connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                      edge_state, node_state, source_idx, target_idx)

            while not connected:
                if total_rate <= 0.0:
                    return np.empty((0, 2), dtype=np.float64)

                dt = np.random.exponential(1.0 / total_rate)
                t_repair += dt
                if t_repair > max_time:
                    print('max_time reached! System couldnt be repaired in time.')
                    return np.empty((0, 2), dtype=np.float64)

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

                connected = dfs_connected(adj_offsets, adj_nodes, adj_edges,
                                          edge_state, node_state, source_idx, target_idx)

            # Store results
            results[cycle_idx, 0] = t_fail
            results[cycle_idx, 1] = t_repair
            cycle_idx += 1

        return results

    @njit
    def simulate_numba_core_norepair(n_edges, n_nodes,
                                     adj_offsets, adj_nodes, adj_edges,
                                     source_idx, target_idx,
                                     lam_edges_arr, lam_nodes_arr):
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
        edge_state = np.ones(n_edges, dtype=np.bool)
        node_state = np.ones(n_nodes, dtype=np.bool)

        # Build event list
        n_events = n_edges + n_nodes
        rates = np.empty(n_events, dtype=np.float64)

        # build list of rates
        for i in range(n_edges):
            rates[i] = lam_edges_arr[i]
        for j in range(n_nodes):
            rates[n_edges + j] = lam_nodes_arr[j]

        # Build Fenwick Tree
        bit = bit_build_from_array(rates)
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
    # Wrappers for parallel code execution
    # ------------------------------------------------------------------------------------------------------------------
    @njit(parallel=True)
    def run_parallel_simulations(n_sims,
                                 n_edges, n_nodes,
                                 adj_offsets, adj_nodes, adj_edges,
                                 source_idx, target_idx,
                                 lam_edges_arr, lam_nodes_arr,
                                 mu_edges_arr, mu_nodes_arr,
                                 max_cycles, max_time, Laziness=0):
        """
        Run n_sims in parallel.
        Uses all N CPU-Cores to each run n_sims/N simulation runs
        Speedup: ~Nx with N Cores.
        """
        all_results = np.empty((n_sims, 2), dtype=np.float64)

        # core parallelisation routine
        for sim_idx in prange(n_sims):
            results = simulate_numba_core(
                n_edges, n_nodes,
                adj_offsets, adj_nodes, adj_edges,
                source_idx, target_idx,
                lam_edges_arr, lam_nodes_arr,
                mu_edges_arr, mu_nodes_arr,
                max_cycles, max_time, Laziness
            )
            #
            if results.shape[0] > 0:
                all_results[sim_idx, 0] = float(np.mean(results[:,0]))
                all_results[sim_idx, 1] = float(np.mean(results[:,1]))
            else:
                # Markiere als invalid
                all_results[sim_idx, :] = np.nan

        return all_results

    @njit(parallel=True)
    def run_parallel_simulations_norepair(n_sims,
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

        # core parallelisation routine
        for sim_idx in prange(n_sims):
            results = simulate_numba_core_norepair(
                n_edges, n_nodes,
                adj_offsets, adj_nodes, adj_edges,
                source_idx, target_idx,
                lam_edges_arr, lam_nodes_arr
            )
            # TODO: rewrite such that mean over max_cycles is appended.
            if results is not None:
                all_results[sim_idx] = results
            else:
                # Markiere als invalid
                all_results[sim_idx] = np.nan

        return all_results


    # ------------------------------------------------------------------------------------------------------------------
    # Graph Conversion Helper
    # ------------------------------------------------------------------------------------------------------------------
    def graph_to_numba_arrays(G, source, target):
        """
        Convert NetworkX graph to Numba-compatible np.arrays

        :INPUT:
            **G**       - networkx.Graph, topology of network
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


# =====================================================================================
# PYTHON-ONLY VERSION (Union-Find)
# =====================================================================================
def simulate_cycle_repairable(G, source, target,
                              lam_edges, lam_nodes,
                              mu_edges, mu_nodes,
                              max_cycles=1, max_time=1e6):
    """
    Python version with Union-Find (original implementation).
    """
    edge_list = list(G.edges())
    node_list = list(G.nodes())

    edge_state = [1] * len(edge_list)
    node_state = [1] * len(node_list)

    edge_index = {e: i for i, e in enumerate(edge_list)}
    node_index = {n: i for i, n in enumerate(node_list)}

    events = []
    for i, e in enumerate(edge_list):
        events.append(("edge", i, lam_edges[e], mu_edges[e]))
    for i, n in enumerate(node_list):
        events.append(("node", i, lam_nodes[n], mu_nodes[n]))

    total_rate = sum(lam_edges[e] for e in edge_list) + sum(lam_nodes[n] for n in node_list)

    uf = UnionFind(node_list)
    uf.rebuild_uf(edge_list, node_list, edge_state, node_state, node_index)

    needs_rebuild = False

    def run_phase(target_connectivity):
        nonlocal total_rate, needs_rebuild
        t = 0.0

        while True:
            if needs_rebuild:
                uf.rebuild_uf(edge_list, node_list, edge_state, node_state, node_index)
                needs_rebuild = False

            is_connected = uf.connected(source, target)
            if is_connected != target_connectivity:
                break

            if total_rate == 0:
                return None

            dt = random.expovariate(total_rate)
            t += dt
            if t > max_time:
                return None

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

        return t

    results = []
    for _ in range(max_cycles):
        t_fail = run_phase(target_connectivity=True)
        if t_fail is None:
            return None
        t_repair = run_phase(target_connectivity=False)
        if t_repair is None:
            return None
        results.append((t_fail, t_repair))

    if not results:
        return None

    mttf = statistics.mean(r[0] for r in results)
    mttr = statistics.mean(r[1] for r in results)
    return mttf, mttr

def simulate_time_to_failure_norepair(G, source, target, lam_edges, lam_nodes):
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
    A_max, MTTR_max = 1, 0
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
    print('Availability equals one leading to division by zero')
    return 1e8


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
    if not mttr is None:
        fig2, ax2, res2 = monte_carlo_plotting(mttf=mttr, title="Monte-Carlo Histogramm (MTTR)")

    rng = np.random.default_rng(42)
    samples = rng.normal(loc=0.0, scale=1.0, size=50_000)
    plt.show()
    return fig, ax, result


# ----------------------------------------------------------------------------------------------------------------------
# run N Monte Carlo simulations and estimate reliability metrics from samples
# ----------------------------------------------------------------------------------------------------------------------
def estimate_mttf_mttr(G, source, target, N=1000, max_cycles=1, use_numba=True, Plotting=False, Parallel=True, Laziness=0):
    """
    Run N Monte Carlo simulations and estimate MTTF/MTTR.

    Args:
        G: NetworkX graph with 'mtbf_h' and 'mttr_h' attributes
        source: Source node
        target: Target node
        N: Number of simulations
        max_cycles: Number of UP/DOWN cycles per simulation
        use_numba: Use Numba-optimized version if available (default: True)

    Returns:
        (mttf, mttr): Mean time to failure and mean time to repair
    """
    lam_edges, lam_nodes, mu_edges, mu_nodes = get_lam_mu_from_graph(G)


    # Check for non-repairable case
    if all(v == 0 for v in mu_edges.values()) and all(v == 0 for v in mu_nodes.values()):

        if use_numba and NUMBA_AVAILABLE:
            print(
                f"Using Numba-optimized implementation (Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

            # Convert to arrays
            conv = graph_to_numba_arrays(G, source, target)

            # get edge and node arrays
            lam_edges_arr = np.array([lam_edges[e] for e in conv['edge_list']], dtype=np.float64)
            lam_nodes_arr = np.array([lam_nodes[n] for n in conv['node_list']], dtype=np.float64)


            if Parallel:
                print(f"Running {N} simulations in parallel...")

                all_results = run_parallel_simulations_norepair(N, conv['n_edges'], conv['n_nodes'],
                                                                conv['adj_offsets'], conv['adj_nodes'],
                                                                conv['adj_edges'], conv['source_idx'],
                                                                conv['target_idx'], lam_edges_arr, lam_nodes_arr)
                # Filter valid results
                valid_mask = ~np.isnan(all_results)
                valid_results = all_results[valid_mask]

                if valid_results.shape[0] == 0:
                    return None, None

                samples = valid_results
                return statistics.mean(samples), np.inf

            else:
                # Call Numba core and store samples
                samples = [simulate_numba_core_norepair(conv['n_edges'], conv['n_nodes'],
                                                        conv['adj_offsets'], conv['adj_nodes'],
                                                        conv['adj_edges'], conv['source_idx'],
                                                        conv['target_idx'], lam_edges_arr, lam_nodes_arr)
                           for _ in range(N)]
                return statistics.mean(samples), np.inf

        # Union-Find Fallback
        samples = [simulate_time_to_failure_norepair(G, source, target, lam_edges, lam_nodes)
                       for _ in range(N)]
        return statistics.mean(samples), np.inf

    # Check for no-failure case
    elif all(v == 0 for v in lam_edges.values()) and all(v == 0 for v in lam_nodes.values()):
        # TODO!
        return np.inf, 0.0

    # calc max_time
    max_time = calc_max_time(lam_edges, lam_nodes, mu_edges, mu_nodes)

    mttf_samples, mttr_samples = [], []

    # Repairable case: choose implementation
    if use_numba and NUMBA_AVAILABLE:
        # Use Numba version
        print(f"Using Numba-optimized implementation (Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

        # Array conversion
        conv = graph_to_numba_arrays(G, source, target)
        lam_edges_arr = np.array([lam_edges[e] for e in conv['edge_list']], dtype=np.float64)
        mu_edges_arr = np.array([mu_edges[e] for e in conv['edge_list']], dtype=np.float64)
        lam_nodes_arr = np.array([lam_nodes[n] for n in conv['node_list']], dtype=np.float64)
        mu_nodes_arr = np.array([mu_nodes[n] for n in conv['node_list']], dtype=np.float64)

        if Parallel:
            print(f"Running {N*max_cycles} simulations in parallel...")

            # Parallel execution!
            all_results = run_parallel_simulations(
                N,
                conv['n_edges'], conv['n_nodes'],
                conv['adj_offsets'], conv['adj_nodes'], conv['adj_edges'],
                conv['source_idx'], conv['target_idx'],
                lam_edges_arr, lam_nodes_arr, mu_edges_arr, mu_nodes_arr,
                max_cycles, 1e6, Laziness
            )

            # Filter valid results
            valid_mask = ~np.isnan(all_results[:, 0])
            valid_results = all_results[valid_mask]

            if valid_results.shape[0] == 0:
                return None, None

            mttf_samples = valid_results[:, 0]
            mttr_samples = valid_results[:, 1]

        else:
            # N simulations with preconverted arrays
            for _ in range(N):
                results = simulate_numba_core(
                    conv['n_edges'],
                    conv['n_nodes'],
                    conv['adj_offsets'],
                    conv['adj_nodes'],
                    conv['adj_edges'],
                    conv['source_idx'],
                    conv['target_idx'],
                    lam_edges_arr,
                    lam_nodes_arr,
                    mu_edges_arr,
                    mu_nodes_arr,
                    max_cycles,
                    max_time,
                    Laziness
                )

                # check if results not empty and append to lists
                if results.shape[0] > 0:
                    # append mean over max_cycles deep run
                    mttf_samples.append(float(np.mean(results[:, 0])))
                    mttr_samples.append(float(np.mean(results[:, 1])))

    else:
        # Python version
        print(f"Using Python implementation (Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")

        for _ in range(N):
            res = simulate_cycle_repairable(G, source, target, lam_edges, lam_nodes,
                                            mu_edges, mu_nodes, max_cycles=max_cycles)
            if res is not None:
                tf, tr = res
                mttf_samples.append(tf)
                mttr_samples.append(tr)

        mttf_samples = np.array(mttf_samples)
        mttr_samples = np.array(mttr_samples)

    # check if samples empty
    if len(mttf_samples) == 0:
        return None, None

    # Plot results (optional)
    if Plotting:
        monte_carlo_plotting(mttf_samples, mttr_samples)

    # return mean
    return float(np.mean(mttf_samples)), float(np.mean(mttr_samples))