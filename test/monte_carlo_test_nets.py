'''
@authors: fnuetz
'''
import networkx as nx

# ----------------------------------------------------------------------------------------------------------------------
# Implementation of some basic network topologies to run
# ----------------------------------------------------------------------------------------------------------------------
# 4Net_11:
def N4_11(mttf_h_nodes, mttf_h_edges, mttr_h_nodes, mttr_h_edges):

    G = nx.Graph()
    G.add_nodes_from([
        ("S", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("A", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("B", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("T", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes})
    ])
    G.add_edges_from([
        ("S", "A", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("A", "T", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("S", "B", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("B", "T", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges})
    ])

    return G

# 4Net_21
def N4_21():
    G = nx.Graph()
    G.add_edges_from([
        ("S", "A"), ("A", "T"),
        ("S", "B"), ("B", "T"),
        ("A", "B")
    ])
    mtbf_h = {
        ("S", "A"): 1,
        ("A", "T"): 1,
        ("S", "B"): 1,
        ("T", "B"): 1,
        ("A", "B"): 1
    }
    mttr_h = {
        ("S", "A"): 1e-1,
        ("A", "T"): 1e-1,
        ("S", "B"): 0,
        ("T", "B"): 0,
        ("A", "B"): 0
    }
    print('---WARNING: Legacy Network---')
    return G, mtbf_h, mttr_h

# 4Net_22
def N4_22():
    G = nx.Graph()
    G.add_edges_from([
        ("S", "A"), ("A", "T"),
        ("S", "B"), ("B", "T"),
        ("S", "T")
    ])
    mtbf_h = {
        ("S", "A"): 1,
        ("A", "T"): 1,
        ("S", "B"): 1,
        ("T", "B"): 1,
        ("S", "T"): 1
    }
    mttr_h = {
        ("S", "A"): 1e-1,
        ("A", "T"): 1e-1,
        ("S", "B"): 1e-1,
        ("T", "B"): 1e-1,
        ("S", "T"): 1e-1
    }
    print('---WARNING: Legacy Network---')
    return G, mtbf_h, mttr_h

# 4Net_31
def N4_31():
    G = nx.Graph()
    G.add_nodes_from([
        ("S", {'mttf_h': 1, 'mttr_h': 10}),
        ("A", {'mttf_h': 1, 'mttr_h': 10}),
        ("B", {'mttf_h': 1, 'mttr_h': 10}),
        ("T", {'mttf_h': 1, 'mttr_h': 10})
    ])

    G.add_edges_from([
        ("S", "A", {'mttf_h': 0.1, 'mttr_h': 1}),
        ("A", "T", {'mttf_h': 0.1, 'mttr_h': 1}),
        ("S", "B", {'mttf_h': 0.1, 'mttr_h': 1}),
        ("B", "T", {'mttf_h': 0.1, 'mttr_h': 1}),
        ("S", "T", {'mttf_h': 0.1, 'mttr_h': 1}),
        ("A", "B", {'mttf_h': 0.1, 'mttr_h': 1})
    ])

    return G

# 6N-seriell
def N6_seriell(mttf_h_nodes, mttf_h_edges, mttr_h_nodes, mttr_h_edges):

    G = nx.Graph()

    G.add_nodes_from([
        ("S", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("1", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("2", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("3", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("4", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("5", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("T", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes})
    ])

    G.add_edges_from([
        ("S", "1", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("1", "2", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("2", "3", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("3", "4", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("4", "5", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("5", "T", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges})
    ])

    return G

#
def oneNet():
    G = nx.Graph()
    G.add_edges_from([
        ("S", "T")
    ])
    mtbf_h = {
        ("S", "T"): 0
    }
    mttr_h = {
        ("S", "T"): 1.0
    }
    print('---WARNING: Legacy Network---')
    return G, mtbf_h, mttr_h

#
def N3_parallel(mttf_h_nodes, mttf_h_edges, mttr_h_nodes, mttr_h_edges):

    G = nx.Graph()
    G.add_nodes_from([
        ("S", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("A", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("B", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("C", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("T", {'mttf_h': mttf_h_nodes, 'mttr_h': mttr_h_nodes})
    ])
    G.add_edges_from([
        ("S", "A", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("A", "T", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("S", "B", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("B", "T", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("S", "C", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges}),
        ("C", "T", {'mttf_h': mttf_h_edges, 'mttr_h': mttr_h_edges})
    ])

    return G


# pandapower-pandaICT-connector
def pp_pi_connector():
    G = nx.Graph()
    G.add_edges_from([
        ("CC", "1"), ("1", "2"),
        ("2", "conv1"), ("conv1", "pc1"),
        ("2", "conv2"), ("conv2", "pc2"),
        ("2", "conv3"), ("conv3", "sc"),
        ("2", "pq1"),
        ("2", "pq2")
    ])
    mtbf_h = {
        ("CC", "1"):    1.0,
        ("1", "2"):     1.0,
        ("2", "conv1"): 1.0,
        ("conv1", "pc1"): 1.0,
        ("2", "conv2"): 1.0,
        ("conv2", "pc2"): 1.0,
        ("2", "conv3"): 1.0,
        ("conv3", "sc"): 1.0,
        ("2", "pq1"):   1.0,
        ("2", "pq2"):   1.0
    }
    mttr_h = {
        ("CC", "1"): 1.0,
        ("1", "2"): 1.0,
        ("2", "conv1"): 1.0,
        ("conv1", "pc1"): 1.0,
        ("2", "conv2"): 1.0,
        ("conv2", "pc2"): 1.0,
        ("2", "conv3"): 1.0,
        ("conv3", "sc"): 1.0,
        ("2", "pq1"): 1.0,
        ("2", "pq2"): 1.0
    }
    print('---WARNING: Legacy Network---')
    return G, mtbf_h, mttr_h


def two_sources_independent(mttf_n, mttf_e, mttr_n, mttr_e):
    """
    Two independent sources and paths to one target.

    Topology:
        S1 -[e1]- A -[e2]- T
        S2 -[e3]- B -[e4]- T

    For simplicity S1, S2, T cant fail
    """
    G = nx.Graph()

    # unfailing nodes
    G.add_node("S1", mttf_h=0, mttr_h=0)
    G.add_node("S2", mttf_h=0, mttr_h=0)
    G.add_node("T", mttf_h=0, mttr_h=0)

    # nodes on path
    G.add_node("A", mttf_h=mttf_n, mttr_h=mttr_n)
    G.add_node("B", mttf_h=mttf_n, mttr_h=mttr_n)

    # edges
    G.add_edge("S1", "A", mttf_h=mttf_e, mttr_h=mttr_e)  # e1
    G.add_edge("A", "T", mttf_h=mttf_e, mttr_h=mttr_e)  # e2
    G.add_edge("S2", "B", mttf_h=mttf_e, mttr_h=mttr_e)  # e3
    G.add_edge("B", "T", mttf_h=mttf_e, mttr_h=mttr_e)  # e4

    return G


def two_sources_shared_component(mttf_n, mttf_e, mttr_n, mttr_e):
    """
    Two paths with shared component C.

    Topology:
        S1 -[e1]- A -[e3]-+
                          C -[e5]- T
        S2 -[e2]- B -[e4]-+

    S1, S2, T cant fail.
    """
    G = nx.Graph()

    # unfailing nodes
    G.add_node("S1", mttf_h=0, mttr_h=0)
    G.add_node("S2", mttf_h=0, mttr_h=0)
    G.add_node("T", mttf_h=0, mttr_h=0)

    # nodes on path
    G.add_node("A", mttf_h=mttf_n, mttr_h=mttr_n)
    G.add_node("B", mttf_h=mttf_n, mttr_h=mttr_n)
    G.add_node("C", mttf_h=mttf_n, mttr_h=mttr_n)  # Shared!

    # edges
    G.add_edge("S1", "A", mttf_h=mttf_e, mttr_h=mttr_e)  # e1
    G.add_edge("S2", "B", mttf_h=mttf_e, mttr_h=mttr_e)  # e2
    G.add_edge("A", "C", mttf_h=mttf_e, mttr_h=mttr_e)  # e3
    G.add_edge("B", "C", mttf_h=mttf_e, mttr_h=mttr_e)  # e4
    G.add_edge("C", "T", mttf_h=mttf_e, mttr_h=mttr_e)  # e5

    return G


def two_sources_two_targets_independent(mttf_n, mttf_e, mttr_n, mttr_e):
    """
    4 independent paths

    Topology:
        S1 --- A --- T1_a
        S1 --- B --- T2_a
        S2 --- C --- T1_b
        S2 --- D --- T2_b

    Each source-target pair has its own target node to prevent cross-connections.
    """
    G = nx.Graph()

    # Source nodes
    G.add_node("S1", mttf_h=0, mttr_h=0)
    G.add_node("S2", mttf_h=0, mttr_h=0)

    # individual target nodes for each path to avoid cross-connections
    G.add_node("T1_a", mttf_h=0, mttr_h=0)  # S1's T1
    G.add_node("T2_a", mttf_h=0, mttr_h=0)  # S1's T2
    G.add_node("T1_b", mttf_h=0, mttr_h=0)  # S2's T1
    G.add_node("T2_b", mttf_h=0, mttr_h=0)  # S2's T2

    #  nodes
    G.add_node("A", mttf_h=mttf_n, mttr_h=mttr_n)
    G.add_node("B", mttf_h=mttf_n, mttr_h=mttr_n)
    G.add_node("C", mttf_h=mttf_n, mttr_h=mttr_n)
    G.add_node("D", mttf_h=mttf_n, mttr_h=mttr_n)

    # Edges - completely isolated paths
    G.add_edge("S1", "A", mttf_h=mttf_e, mttr_h=mttr_e)
    G.add_edge("A", "T1_a", mttf_h=mttf_e, mttr_h=mttr_e)

    G.add_edge("S1", "B", mttf_h=mttf_e, mttr_h=mttr_e)
    G.add_edge("B", "T2_a", mttf_h=mttf_e, mttr_h=mttr_e)

    G.add_edge("S2", "C", mttf_h=mttf_e, mttr_h=mttr_e)
    G.add_edge("C", "T1_b", mttf_h=mttf_e, mttr_h=mttr_e)

    G.add_edge("S2", "D", mttf_h=mttf_e, mttr_h=mttr_e)
    G.add_edge("D", "T2_b", mttf_h=mttf_e, mttr_h=mttr_e)

    return G