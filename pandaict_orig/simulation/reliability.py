import pandapower as pp
import random
import pandapower.topology as top

import pandaict_orig.outage
import pandaict_orig.topology as ict_top
from pandaict_orig.simulation.toolbox import get_extended_protection_infos
import pandaict_orig as pi
import pandas as pd

import numba


def calculate_reliability(net, ict_net, extended_line_information=None):
    extended_line_information = extended_line_information or get_extended_protection_infos(
        net)
    weights, rlps, rlfl = calculate_weights(
        net, ict_net, extended_line_information)
    t_loc = 75

    res_load_rel = dict()
    res_line_rel = dict()

    for load, p_kw in zip(net.load.index, net.load.p_kw):
        res_load_rel[load] = {"p_kw": p_kw,
                              "out_time_expect": 0, "out_kwh_expect": 0}

    for idx, line in net.line.iterrows():
        res_line_rel[idx] = {"h": line.h_per_km
                             * line.length_km, "out_kwh_expect": 0}

    switch_times = pi.pandas_to_dict(net.switch.index, net.switch.time_min)
    switch_times_manual = pi.pandas_to_dict(
        net.switch.index, net.switch.time_manual_min)

    mttr_lines = pi.pandas_to_dict(net.line.index, net.line.mttr)
    if ict_net:
        mttr_links = pi.pandas_to_dict(ict_net.link.index, ict_net.link.mttr)

    for failure, weight in weights.items():
        #print(failure, weight)
        if not isinstance(failure, tuple):
            prot_sw = extended_line_information[failure]["protection_switches"]
            res_sw = extended_line_information[failure]["resupply_switches"]
            iso_sw = extended_line_information[failure]["isolation_switches"]

            t_rep = mttr_lines[failure]
            t_isolation = t_loc / 60
            for sw in iso_sw:
                t_isolation += switch_times[sw] / 60
            t_resup = t_isolation
            for sw in res_sw:
                t_resup += switch_times[sw] / 60

            iso_loads = extended_line_information[failure]["isolated_loads"]
            prot_loads = extended_line_information[failure]["protected_loads"]
            res_loads = extended_line_information[failure]["resupplied_loads"]

            isolated_kwh = 0
            for load in iso_loads:
                res_load_rel[load]["out_time_expect"] += t_rep * weight
                isolated_kwh += res_load_rel[load]["p_kw"] * t_rep * weight
            protected_kwh = 0
            for load in prot_loads:
                res_load_rel[load]["out_time_expect"] += t_isolation * weight
                protected_kwh += res_load_rel[load]["p_kw"] * \
                    t_isolation * weight
            resupplied_kwh = 0
            for load in res_loads:
                res_load_rel[load]["out_time_expect"] += t_resup * weight
                resupplied_kwh += res_load_rel[load]["p_kw"] * t_resup * weight

            res_line_rel[failure]["out_kwh_expect"] = isolated_kwh + \
                protected_kwh + resupplied_kwh
        else:
            prot_sw = extended_line_information[failure[0]
                                                ]["protection_switches"]
            res_sw = extended_line_information[failure[0]]["resupply_switches"]
            iso_sw = extended_line_information[failure[0]
                                               ]["isolation_switches"]

            failed_switches = get_failed_switches_per_link(failure[1], rlps)

            t_rep = min(mttr_lines[failure[0]], mttr_links[failure[1]])
            t_isolation = t_loc / 60
            for sw in set(iso_sw) - set(failed_switches):
                t_isolation += switch_times[sw] / 60
            for sw in set(iso_sw) & set(failed_switches):
                t_isolation += switch_times_manual[sw] / 60
            t_resup = t_isolation
            for sw in set(res_sw) - set(failed_switches):
                t_resup += switch_times[sw] / 60
            for sw in set(res_sw) & set(failed_switches):
                t_resup += switch_times_manual[sw] / 60

            iso_loads = extended_line_information[failure[0]]["isolated_loads"]
            prot_loads = extended_line_information[failure[0]
                                                   ]["protected_loads"]
            res_loads = extended_line_information[failure[0]
                                                  ]["resupplied_loads"]

            for load in iso_loads:
                res_load_rel[load]["out_time_expect"] += t_rep * weight
            for load in prot_loads:
                res_load_rel[load]["out_time_expect"] += t_isolation * weight
            for load in res_loads:
                res_load_rel[load]["out_time_expect"] += t_resup * weight

    for idx, data in res_load_rel.items():
        res_load_rel[idx]["out_kwh_expect"] = data["p_kw"] * \
            data["out_time_expect"]

    return res_load_rel, res_line_rel


def calculate_weights(net, ict_net, extended_line_information):
    weights = dict()
    # if no ict_net is specified return only the line weights
    if not ict_net:
        in_service_lines = net.line.index[net.line.in_service]
        for line in in_service_lines:
            h_line = extended_line_information[line]["h"]
            weights[line] = h_line
        return weights, None, None

    # if no required links for any line were found, only return the line weights
    rlfl, rlps = relevant_links_for_line(
        net, ict_net, extended_line_information)
    if not rlfl:
        in_service_lines = net.line.index[net.line.in_service]
        for line in in_service_lines:
            h_line = extended_line_information[line]["h"]
            weights[line] = h_line
        return weights, None, None

    h_per_km_links = pi.pandas_to_dict(
        ict_net.link.index, ict_net.link.h_per_km)
    length_km_links = pi.pandas_to_dict(
        ict_net.link.index, ict_net.link.length_km)
    mttr_links = pi.pandas_to_dict(ict_net.link.index, ict_net.link.mttr)
    mttr_lines = pi.pandas_to_dict(net.line.index, net.line.mttr)
    for line, links in rlfl.items():
        h_line = extended_line_information[line]["h"]
        mttr_line = mttr_lines[line]
        p_line = P(h_line, mttr_line)
        line_factor = 1

        for link in links:
            h_link = h_per_km_links[link] * length_km_links[link]
            mttr_link = mttr_links[link]
            p_link = P(h_link, mttr_link)
            line_factor -= p_line * p_link
            weight_line_link = 0.5*(h_line*p_link + h_link*p_line)
            weights[(line, link)] = weight_line_link
        weight_line = h_line * line_factor
        weights[line] = weight_line

    return weights, rlps, rlfl


def relevant_links_for_line(net, ict_net, extended_line_information):
    required_links_per_switch = get_required_links_per_switch(ict_net)

    rlfl = dict()

    relevant_switches_per_line = dict()
    for i, rlrx in extended_line_information.items():
        relevant_switches_per_line[i] = rlrx["protection_switches"] | rlrx["isolation_switches"] |\
                                        rlrx["resupply_switches"]

        for sw in relevant_switches_per_line[i]:
            if rlfl.get(i):
                if required_links_per_switch.get(sw):
                    rlfl[i].update(required_links_per_switch[sw])
            else:
                if required_links_per_switch.get(sw):
                    rlfl[i] = set(required_links_per_switch[sw])
                else:
                    rlfl[i] = set()
    return rlfl, required_links_per_switch


def get_required_links_per_client(ict_net):
    mg = ict_top.create_ict_graph(ict_net)

#    sc = dict()
#    for i, node in zip(ict_net.client.index, ict_net.client.node):
#        sc[i] = {"node": node}

#    clients = ict_net.client[ict_net.client.et == "switch"]
    clients = ict_net.client
    clients_dict = {i: {"node": node, "server": server, "element": element}
                    for i, node, server, element in
                    zip(clients.index,
                        clients.node,
                        clients.server,
                        clients.element)}
    required_links = set()

    bridges_per_server = dict()
    for server in {sc["server"] for sc in clients_dict.values()}:
        bridges_per_server[server] = top.find_graph_characteristics(
            mg, [ict_net.server.node.loc[server]], ["required_bridges"])["required_bridges"]
    bridges_per_client = dict()
    for i, cl in clients_dict.items():
        bridge_nodes = set()
        if bridges_per_server.get(cl["server"]) and bridges_per_server.get(cl["server"]).get(cl["node"]):
            for nodes in bridges_per_server[cl["server"]][cl["node"]]:
                bridge_nodes.update(nodes)

        if bridge_nodes:
            bridges_per_client[cl["element"]
                               ] = get_links_from_nodes(mg, bridge_nodes)
            required_links.update(bridges_per_client[cl["element"]])

    return bridges_per_client, required_links


def get_links_from_nodes(mg, nodes):
    links = set()
    for edge in mg.edges():
        if len(set(edge) & set(nodes)) == 2:
            links.add(list(mg[edge[0]][edge[1]].values())[0]["key"])
    return links


def get_failed_switches_per_link(link, rlps):
    failed_switches = []
    for switch, links in rlps.items():
        if link in links:
            failed_switches.append(switch)

    return failed_switches


def P(h, mttr):
    return h*mttr/8760


##############################
############ OLD #############
##############################

def chose_oos_indices(index):
    index_count = len(index)
    oos_count = random.randint(0, index_count)

    oos_indices = []

    for i in range(oos_count):
        rand_index = -1
        while rand_index == -1 or index[rand_index] in oos_indices:
            rand_index = random.randint(0, index_count-1)
        oos_indices.append(index[rand_index])
    return oos_indices


def test_net(net, ict_net):
    with open("log.txt", "a") as f:
        f.write("new run\n")
    for table in ["bus", "line", "gen", "sgen", "load", "trafo"]:
        oos_indices = chose_oos_indices(net[table].index)
        net[table].in_service.loc[oos_indices] = False
        with open("log.txt", "a") as f:
            f.write("%s: %s\n" % (table, net[table].in_service.tolist()))

    for table in ["node", "link", "server", "client"]:
        oos_indices = chose_oos_indices(ict_net[table].index)
        ict_net[table].in_service.loc[oos_indices] = False
        with open("log.txt", "a") as f:
            f.write("%s: %s\n" % (table, ict_net[table].in_service.tolist()))

    if all(net.bus.in_service.loc[net.ext_grid.bus] == False):
        message = "slack node(s) %s disconnected, net in fail state" \
                % list(net.ext_grid.index[net.bus.in_service[net.ext_grid.bus] == False])
        print(message)
        with open("log.txt", "a") as f:
            f.write(message + "\n\n")
        return

    unsupplied_buses = top.unsupplied_buses(net)

    if unsupplied_buses:
        message = "buses %s unsupplied, net in fail state" % unsupplied_buses
        print(message)
        with open("log.txt", "a") as f:
            f.write(message + "\n\n")
        return

    pp.runpp(net)
    print(net.res_bus)
    with open("log.txt", "a") as f:
        message = "%s" % net.res_bus
        f.write(message + "\n")

    with open("log.txt", "a") as f:
        f.write("\n")
