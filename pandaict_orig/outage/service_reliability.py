from pandaict_orig import topology as pi_top
import pandapower.topology as top
import copy
import networkx as nx
from collections import defaultdict
import numpy as np
from itertools import combinations


def get_graph_and_characteristics(net, prot):
    mg = pi_top.create_ict_graph(net, prot)

    # add auxiliary node and edge for articulation_point determination
    free_idx = max(list(mg.nodes)) + 1
    mg.add_edge(free_idx, list(mg.nodes)[0])

    char = top.find_graph_characteristics(
        mg,
        roots=[free_idx],
        characteristics=[
            "connected", "articulation_points", "bridges", "stub_buses",
            "required_bridges", "notn1_areas"
        ]
    )

    # remove auxiliary node and edge
    mg.remove_node(free_idx)

    # remove auxiliary edge from bridges
    char["bridges"] = {bridge for bridge in char["bridges"]
                       if free_idx not in bridge}

    return mg, char["bridges"], char["articulation_points"]


def get_failure_probabilites(mg, net, failure_combinations):
    combs = failure_combinations
    shape = np.array(combs).shape
    row_count = shape[0]
    column_count = shape[1] if len(shape) > 1 else 1
    probabilites = np.ones(row_count)

    for i in range(column_count):
        column = [mg[comb[i][0]][comb[i][1]][0]["key"] for comb in combs]
        probabilites *= net.link.h_per_km.loc[column].values * \
            net.link.length_km.loc[column].values

    return dict(zip(combs, probabilites))


def get_failed_services(mg, net, probabilites, prot):
    mg_copy = copy.deepcopy(mg)
    for failure, prob in probabilites.items():
        mg_copy.remove_edges_from(failure)
        cc = list(nx.connected_components(mg_copy))
        for i, service in net.service[net.service.protocol == prot].iterrows():
            device_count = len(net.device[net.device.service == i])
            mcpf = True if service.minimum_connected_percent else False
            rcf = True if service.required_connected else False
            for c in cc:
                devices = net.device.index[(net.device.node.isin(c)) & (
                    net.device.service == i)]
                if service.minimum_connected_percent:
                    if len(devices)/device_count * 100 >= service.minimum_connected_percent:
                        mcpf = False
                        break
                if service.required_connected:
                    if not set(service.required_connected) - set(c):
                        rcf = False
                        break
            if mcpf or rcf:
                mttr_sum = sum([net.link.mttr_h.at[mg[fn][tn][0]["key"]]
                               for fn, tn in failure])
                net.res_rel_service.outage_time_h.at[i] += prob * mttr_sum


def assess_service_reliability(net, probability_threshold=None):
    # determine protocols used in net
    protocols = set()
    for prot in net.link.protocols.values:
        protocols.update(prot)

    for prot in protocols:
        mg, bridges, articulation_points = get_graph_and_characteristics(
            net, prot)
        level = 1
        while True:
            failure_combinations = list(combinations(bridges, level))
            if not failure_combinations:
                break
            probabilites = get_failure_probabilites(
                mg, net, failure_combinations)
            if probability_threshold is not None and \
                    all(np.array(list(probabilites.values())) < probability_threshold):
                break
            get_failed_services(mg, net, probabilites, prot)

            level += 1
