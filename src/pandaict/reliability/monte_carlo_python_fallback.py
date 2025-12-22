'''
# Copyright (c) 2016-2025 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.12.2025

@author: fnuetz
'''

import random
import statistics
import numpy as np

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
                results.append((np.inf, 0.0))
                return results
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
                results.append((t_fail, np.inf))
                return results

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