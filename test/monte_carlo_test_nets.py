'''
@authors: fnuetz
'''
import networkx as nx

# ----------------------------------------------------------------------------------------------------------------------
# Implementation of some basic network topologies to run
# ----------------------------------------------------------------------------------------------------------------------
# 4Net_11:
def N4_11(mtbf_h_nodes, mtbf_h_edges, mttr_h_nodes, mttr_h_edges):

    G = nx.Graph()
    G.add_nodes_from([
        ("S", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("A", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("B", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("T", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes})
    ])
    G.add_edges_from([
        ("S", "A", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("A", "T", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("S", "B", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("B", "T", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges})
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
        ("S", {'mtbf_h': 1, 'mttr_h': 10}),
        ("A", {'mtbf_h': 1, 'mttr_h': 10}),
        ("B", {'mtbf_h': 1, 'mttr_h': 10}),
        ("T", {'mtbf_h': 1, 'mttr_h': 10})
    ])

    G.add_edges_from([
        ("S", "A", {'mtbf_h': 0.1, 'mttr_h': 1}),
        ("A", "T", {'mtbf_h': 0.1, 'mttr_h': 1}),
        ("S", "B", {'mtbf_h': 0.1, 'mttr_h': 1}),
        ("B", "T", {'mtbf_h': 0.1, 'mttr_h': 1}),
        ("S", "T", {'mtbf_h': 0.1, 'mttr_h': 1}),
        ("A", "B", {'mtbf_h': 0.1, 'mttr_h': 1})
    ])

    return G

# 6N-seriell
def N6_seriell(mtbf_h_nodes, mtbf_h_edges, mttr_h_nodes, mttr_h_edges):

    G = nx.Graph()

    G.add_nodes_from([
        ("S", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("1", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("2", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("3", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("4", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("5", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("T", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes})
    ])

    G.add_edges_from([
        ("S", "1", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("1", "2", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("2", "3", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("3", "4", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("4", "5", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("5", "T", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges})
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
def N3_parallel(mtbf_h_nodes, mtbf_h_edges, mttr_h_nodes, mttr_h_edges):

    G = nx.Graph()
    G.add_nodes_from([
        ("S", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("A", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("B", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("C", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes}),
        ("T", {'mtbf_h': mtbf_h_nodes, 'mttr_h': mttr_h_nodes})
    ])
    G.add_edges_from([
        ("S", "A", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("A", "T", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("S", "B", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("B", "T", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("S", "C", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges}),
        ("C", "T", {'mtbf_h': mtbf_h_edges, 'mttr_h': mttr_h_edges})
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