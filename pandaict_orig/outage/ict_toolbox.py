import networkx as nx
import pandaict_orig as pi
import topology as top
from itertools import combinations, chain, product


def switch_index(sw):
    return int(sw.replace("switch_", ""))


def get_unsupplied_nodes(mg, roots):
    not_supplied = set()
    for cc in nx.connected_components(mg):
        if not set(cc) & roots:
            not_supplied.update(set(cc))
    return not_supplied


def get_new_index(array):
    if not array:
        return 0
    else:
        if isinstance(array, list):
            return len(array)
        elif isinstance(array, dict):
            return max(array.keys())+1


def sort_children(children, open_switches):
    children_sorted = []
    for child in children:
        if isinstance(child, str) and switch_index(child) in open_switches:
            children_sorted.insert(0, child)
        else:
            children_sorted.append(child)
    return children_sorted


def merge_areas(area1, area2, protection_areas, isolation_areas, iso_area1, iso_area2,
                protection_area_per_bus):
    # update protection area of iso areas
    area1_iso_areas_graph = protection_areas[area1]["iso_areas_graph"]
    for iso_area in area1_iso_areas_graph.nodes:
        isolation_areas[iso_area]["protection_area"] = area2

    # merge buses and lines
    protection_areas[area2]["buses"] |= protection_areas[area1]["buses"]
    protection_areas[area2]["lines"] |= protection_areas[area1]["lines"]

    # merge resupply areas
    for area, resup_areas in protection_areas[area1]["resupply_areas"].items():
        if area not in protection_areas[area2]["resupply_areas"]:
            protection_areas[area2]["resupply_areas"][area] = resup_areas
        else:
            protection_areas[area2]["resupply_areas"][area].update(resup_areas)

    # join graphs of iso areas
    protection_areas[area2]["iso_areas_graph"] = nx.compose(
        protection_areas[area2]["iso_areas_graph"],
        protection_areas[area1]["iso_areas_graph"]
    )
    protection_areas[area2]["iso_areas_graph"].add_edge(iso_area1, iso_area2)

    # merge protection switches
    protection_areas[area2]["protection_switches"] |= protection_areas[area1]["protection_switches"]

    # update protection areas per bus
    for bus, area in protection_area_per_bus.items():
        if area == area1:
            protection_area_per_bus[bus] = area2

    # delete obsolete area
    del protection_areas[area1]

    return protection_areas, isolation_areas, protection_area_per_bus


def get_isolation_and_protection_areas(net, open_switches, cb_switches, ds_switches):
    g = top.create_switch_nxgraph(net, respect_switches=False)
    roots = net.ext_grid.bus.to_list()

    visited = set()
    visited_end_nodes = set()

    isolation_area_per_bus = dict()
    protection_area_per_bus = dict()

    connected_areas_per_switch = dict()
    open_switches_per_bus = dict()

    isolation_areas = dict()
    protection_areas = dict()
    curr_iso_area = None
    curr_prot_area = None

    if curr_prot_area is None:
        curr_prot_area = get_new_index(protection_areas)
        protection_areas[curr_prot_area] = {"buses": set(),
                                            "lines": set(),
                                            "resupply_areas": dict(),
                                            "protection_switches": set(),
                                            "iso_areas_graph": nx.MultiGraph()}

    if curr_iso_area is None:
        curr_iso_area = get_new_index(isolation_areas)
        isolation_areas[curr_iso_area] = {"buses": set(),
                                          "lines": set(),
                                          "isolation_switches": set(),
                                          "protection_switch": None,
                                          "protection_area": curr_prot_area}

    stack = [(root, root, list(g[root].keys())) for root in roots]
    while stack:
        grandparent, parent, children = stack[-1]

        try:
            child = children.pop()

            if grandparent == child or parent in visited_end_nodes:
                continue

            if isinstance(parent, str):

                sw_idx = switch_index(parent)
                if child in protection_area_per_bus \
                        and sw_idx not in open_switches \
                        and sw_idx not in cb_switches \
                        and protection_area_per_bus[child] != curr_prot_area:
                    protection_areas, isolation_areas, protection_area_per_bus = merge_areas(
                        protection_area_per_bus[child],
                        curr_prot_area,
                        protection_areas,
                        isolation_areas,
                        curr_iso_area,
                        isolation_area_per_bus[child],
                        protection_area_per_bus
                    )
                    curr_prot_area = protection_area_per_bus[child]

                # protection area
                if sw_idx in cb_switches or sw_idx in open_switches:
                    if child not in protection_area_per_bus:
                        next_prot_area = get_new_index(protection_areas)
                        protection_areas[next_prot_area] = {"buses": set(),
                                                            "lines": set(),
                                                            "resupply_areas": dict(),
                                                            "protection_switches": set(),
                                                            "iso_areas_graph": nx.MultiGraph()}
                        if switch_index(parent) in cb_switches:
                            protection_areas[curr_prot_area]["protection_switches"].add(parent)
                            protection_areas[next_prot_area]["protection_switches"].add(parent)
                        if switch_index(parent) in open_switches:
                            if protection_areas[curr_prot_area]["resupply_areas"].get(next_prot_area):
                                protection_areas[curr_prot_area]["resupply_areas"][next_prot_area].add(parent)
                            else:
                                protection_areas[curr_prot_area]["resupply_areas"][next_prot_area] = {parent}
                            if protection_areas[next_prot_area]["resupply_areas"].get(curr_prot_area):
                                protection_areas[next_prot_area]["resupply_areas"][curr_prot_area].add(parent)
                            else:
                                protection_areas[next_prot_area]["resupply_areas"][curr_prot_area] = {parent}
                        curr_prot_area = next_prot_area
                    else:
                        child_protection_area = protection_area_per_bus[child]
                        if switch_index(parent) in cb_switches:
                            protection_areas[curr_prot_area]["protection_switches"].add(parent)
                            protection_areas[child_protection_area]["protection_switches"].add(parent)
                        if switch_index(parent) in open_switches:
                            if protection_areas[curr_prot_area]["resupply_areas"].get(child_protection_area):
                                protection_areas[curr_prot_area]["resupply_areas"][child_protection_area].add(parent)
                            else:
                                protection_areas[curr_prot_area]["resupply_areas"][child_protection_area] = {parent}
                            if protection_areas[child_protection_area]["resupply_areas"].get(curr_prot_area):
                                protection_areas[child_protection_area]["resupply_areas"][curr_prot_area].add(parent)
                            else:
                                protection_areas[child_protection_area]["resupply_areas"][curr_prot_area] = {parent}

                # isolation area
                if sw_idx not in ds_switches:
                    isolation_areas[curr_iso_area]["isolation_switches"].add(parent)
                    if child not in isolation_area_per_bus:
                        next_iso_area = get_new_index(isolation_areas)
                        isolation_areas[next_iso_area] = {"buses": set(),
                                                          "lines": set(),
                                                          "isolation_switches": {parent},
                                                          "protection_switch": None,
                                                          "protection_area": curr_prot_area}
                        # add next iso area as node to graph
                        protection_areas[curr_prot_area]["iso_areas_graph"].add_node(next_iso_area)

                        if grandparent in isolation_area_per_bus:
                            iso_area_grandparent = isolation_area_per_bus[grandparent]
                            isolation_areas[iso_area_grandparent]["isolation_switches"].add(parent)
                            if sw_idx not in open_switches and sw_idx not in cb_switches:
                                protection_areas[curr_prot_area]["iso_areas_graph"].add_edge(iso_area_grandparent, next_iso_area)
                        elif sw_idx not in open_switches and sw_idx not in cb_switches:
                            protection_areas[curr_prot_area]["iso_areas_graph"].add_edge(curr_iso_area, next_iso_area)
                        curr_iso_area = next_iso_area
                    else:
                        child_iso_area = isolation_area_per_bus[child]
                        isolation_areas[child_iso_area]["isolation_switches"].add(parent)

            # determine current iso and prot area and add bus
            if isinstance(parent, int):
                if parent in isolation_area_per_bus:
                    curr_iso_area = isolation_area_per_bus[parent]
                else:
                    isolation_area_per_bus[parent] = curr_iso_area
                isolation_areas[curr_iso_area]["buses"].add(parent)

                if parent in protection_area_per_bus:
                    curr_prot_area = protection_area_per_bus[parent]
                else:
                    protection_area_per_bus[parent] = curr_prot_area
                protection_areas[curr_prot_area]["buses"].add(parent)

            # add line to current iso area
            if g[parent][child][0]["type"] == "l":
                isolation_areas[curr_iso_area]["lines"].add(g[parent][child][0]["key"])
                protection_areas[curr_prot_area]["lines"].add(g[parent][child][0]["key"])

            # add end buses of stubs or start buses of feeders to iso area
            if len(g[child]) == 1 and isinstance(child, int):
                isolation_areas[curr_iso_area]["buses"].add(child)
                protection_areas[curr_prot_area]["buses"].add(child)
                visited_end_nodes.add(child)

            if child not in visited:
                visited.add(child)
                sorted_children = sort_children(g[child].keys(), open_switches)
                stack.append((parent, child, sorted_children))
        except IndexError:
            stack.pop()

    return isolation_areas, protection_areas


def get_isolation_area_data(isolation_areas, protection_areas):
    iso_area_data = dict()

    # assessment of reliability
    for i, prot_area in protection_areas.items():

        if not len(prot_area["lines"]):
            continue

        protection_switch = prot_area["protection_switches"]

        resupply_areas = prot_area["resupply_areas"]
        resupply_switches = set()
        for rs_area in resupply_areas.values():
            resupply_switches.update(rs_area)

        iso_areas_with_resupply_switch = set()
        iso_areas_with_protection_switch = set()
        resup_switches_per_iso_area = dict()
        for n, iso_area in isolation_areas.items():
            if iso_area["protection_area"] != i:
                continue
            if iso_area["isolation_switches"] & resupply_switches:
                iso_areas_with_resupply_switch.add(n)
                resup_switches_per_iso_area[n] = iso_area["isolation_switches"] & resupply_switches
            if iso_area["isolation_switches"] & protection_switch:
                iso_areas_with_protection_switch.add(n)

        g = prot_area["iso_areas_graph"]
        for iso_area in g.nodes():
            if not len(isolation_areas[iso_area]["lines"]):
                continue

            # determine different area groups
            resupplied_areas = []
            resupplied_cb_areas = []
            unsupplied_areas = set()

            switches_of_resupplied_areas = []

            split_areas = top.connected_components(g, notravbuses={iso_area})
            for area in split_areas:
                area -= {iso_area}
                resupplied = False
                if area & iso_areas_with_protection_switch:
                    resupplied_cb_areas.append(area)
                    resupplied = True
                elif area & iso_areas_with_resupply_switch:
                    curr_resupply_switches = set()
                    for a in area & iso_areas_with_resupply_switch:
                        for switch in resup_switches_per_iso_area[a]:
                            curr_resupply_switches.add(switch_index(switch))
                    switches_of_resupplied_areas.append(curr_resupply_switches)
                    resupplied_areas.append(area)
                    resupplied = True
                if not resupplied:
                    unsupplied_areas.update(area)
                unsupplied_areas.add(iso_area)

            # ################ DOUBLE FAILURE ################################
            data = dict()
            data["resupplied_cb_areas"] = resupplied_cb_areas
            data["resupplied_areas"] = resupplied_areas
            data["unsupplied_areas"] = unsupplied_areas
            data["isolation_switches"] = isolation_areas[iso_area]["isolation_switches"]
            data["protection_switch"] = switch_index(list(protection_switch)[0])

            data["resupply_switches"] = switches_of_resupplied_areas
            iso_area_data[iso_area] = data
    return iso_area_data


def ps_ict_failure(net, ict_net, needed_data):
    iso_areas_with_lines = needed_data["iso_areas_with_lines"]
    required_links = needed_data["required_links"]

    isolation_areas = needed_data["isolation_areas"]
    protection_areas = needed_data["protection_areas"]
    iso_area_data = needed_data["iso_area_data"]

    sgens_per_bus = needed_data["sgens_per_bus"]
    client_per_sgen = needed_data["client_per_sgen"]

    loads_per_bus = needed_data["loads_per_bus"]

    required_links_per_client = needed_data["required_links_per_client"]

    client_per_switch = needed_data["client_per_switch"]

    open_switches = needed_data["open_switches"]
    cb_switches = needed_data["cb_switches"]
    ds_switches = needed_data["ds_switches"]

    switch_time_man = needed_data["switch_time_man"]
    switch_time_auto = needed_data["switch_time_auto"]

    supplied_switches = needed_data["supplied_switches"]
    supplied_sgens = needed_data["supplied_sgens"]

    h_per_line = needed_data["h_per_line"]
    h_per_link = needed_data["h_per_link"]

    mttr_per_line = needed_data["mttr_per_line"]
    mttr_per_link = needed_data["mttr_per_link"]

    line_factor = needed_data["line_factor"]
    link_factor = needed_data["link_factor"]


    iso_time_per_load = {load: 0 for load in net.load.index}
    resup_time_per_load = {load: 0 for load in net.load.index}
    repair_time_per_load = {load: 0 for load in net.load.index}

    iso_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    resup_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    repair_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    total_outage_time_per_load = {load: 0 for load in net.load.index}
    p_per_load = net.load.p_mw.to_dict()
    out_mwh_per_load = {load: 0 for load in net.load.index}

    total_outage_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    p_per_sgen = net.sgen.p_mw.to_dict()
    out_mwh_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    t_loc = needed_data["t_loc"]

    iso_ict_failures = product(iso_areas_with_lines, required_links)

    for iso_area, link in iso_ict_failures:
        iso_data = iso_area_data[iso_area]

        resupplied_areas = iso_data["resupplied_areas"]
        resupplied_cb_areas = iso_data["resupplied_cb_areas"]
        protection_switches = iso_data["protection_switch"]
        resupply_switches = iso_data["resupply_switches"]

        consider_combination = False

        sgens_without_ict_connection = set()
        switches_without_ict_connection = set()

        for area in set(chain.from_iterable(resupplied_areas)) | set(chain.from_iterable(resupplied_cb_areas)):
            for bus in isolation_areas[area]["buses"]:
                for sgen in sgens_per_bus[bus]:
                    if sgen in client_per_sgen and client_per_sgen[sgen][0] in required_links_per_client \
                       and link in required_links_per_client[client_per_sgen[sgen][0]]:
                        consider_combination = True
                        sgens_without_ict_connection.add(sgen)

        for switch in {protection_switches} \
                | set(chain.from_iterable(resupply_switches)) \
                | {switch_index(sw) for sw in iso_data["isolation_switches"]}:
            if switch in client_per_switch and client_per_switch[switch][0] in required_links_per_client \
               and link in required_links_per_client[client_per_switch[switch][0]]:
                consider_combination = True
                switches_without_ict_connection.add(switch)

        if not consider_combination:
            continue

        ###########################################################
        # h per isolation area
        h = 0
        t_rep = 0
        p_link = pi.P(h_per_link[link], mttr_per_link[link])
        for line in isolation_areas[iso_area]["lines"]:
            p_line = pi.P(h_per_line[line], mttr_per_line[line])
            weight = (h_per_link[link]*p_line + h_per_line[line]*p_link)*0.5
            line_factor[line] -= weight
            link_factor[link] -= weight
            h += weight
            t_rep = min(mttr_per_line[line], mttr_per_link[link])

        # isolation time
        iso_switches_idxs = {switch_index(switch)
                             for switch in iso_data["isolation_switches"]}
        iso_time = 0
        for switch in iso_switches_idxs - set(open_switches) - set(cb_switches):
            if switch not in switches_without_ict_connection and switch in supplied_switches:
                iso_time += switch_time_auto[switch]
            else:
                iso_time += switch_time_man[switch]
        iso_time += t_loc
        iso_time *= h

        # repair time
        repair_time = t_rep *h

        # resupply time resupply_switches
        resup_time_cb = None
        if iso_data["protection_switch"] not in switches_without_ict_connection and iso_data["protection_switch"] in supplied_switches:
            resup_time_cb = switch_time_auto[iso_data["protection_switch"]]
        else:
            resup_time_cb = switch_time_man[iso_data["protection_switch"]]
        resup_time_cb *= h

        # resupply time protection switches
        resup_time = 0
        for switches in iso_data["resupply_switches"]:
            switch_times = []
            for switch in switches:
                time = switch_time_auto[switch] if not switch in switches_without_ict_connection and switch in supplied_switches else switch_time_man[switch]
                switch_times.append(time)
            min_switch_time = min(switch_times)
            resup_time += min_switch_time
        resup_time *= h

        g = protection_areas[isolation_areas[iso_area]["protection_area"]]["iso_areas_graph"]
        resupplied_areas = iso_data["resupplied_areas"]
        resupplied_cb_areas = iso_data["resupplied_cb_areas"]
        unsupplied_areas = iso_data["unsupplied_areas"]

        # determine outage time per load
        for area_idx in g.nodes():
            area = isolation_areas[area_idx]
            for bus in area["buses"]:
                loads = set(loads_per_bus[bus]) if bus in loads_per_bus else []
                sgens = set(sgens_per_bus[bus]) if bus in sgens_per_bus else []

                for load in loads:
                    if area_idx in set(chain.from_iterable(resupplied_areas)) \
                            | set(chain.from_iterable(resupplied_cb_areas)):
                        iso_time_per_load[load] += iso_time
                    if area_idx in unsupplied_areas:
                        repair_time_per_load[load] += repair_time
                    if area_idx in chain.from_iterable(resupplied_cb_areas):
                        resup_time_per_load[load] += resup_time_cb
                    if area_idx in chain.from_iterable(resupplied_areas):
                        resup_time_per_load[load] += resup_time

                for sgen in sgens:
                    if area_idx in set(chain.from_iterable(resupplied_areas)) \
                            | set(chain.from_iterable(resupplied_cb_areas)):
                        iso_time_per_sgen[sgen] += iso_time
                    if area_idx in unsupplied_areas or sgen in sgens_without_ict_connection or sgen not in supplied_sgens:
                        repair_time_per_sgen[sgen] += repair_time
                    if area_idx in chain.from_iterable(resupplied_cb_areas) and sgen not in sgens_without_ict_connection and sgen in supplied_sgens:
                        resup_time_per_sgen[sgen] += resup_time_cb
                    if area_idx in chain.from_iterable(resupplied_areas) and sgen not in sgens_without_ict_connection and sgen in supplied_sgens:
                        resup_time_per_sgen[sgen] += resup_time

    for load in total_outage_time_per_load.keys():
        total_outage_time_per_load[load] = (iso_time_per_load[load]
                                            + resup_time_per_load[load]
                                            + repair_time_per_load[load]) / 60
        out_mwh_per_load[load] = total_outage_time_per_load[load] * p_per_load[load]

    for sgen in total_outage_time_per_sgen.keys():
        total_outage_time_per_sgen[sgen] = (iso_time_per_sgen[sgen]
                                            + resup_time_per_sgen[sgen]
                                            + repair_time_per_sgen[sgen]) / 60
        out_mwh_per_sgen[sgen] = total_outage_time_per_sgen[sgen] * p_per_sgen[sgen]

    return sum(out_mwh_per_load.values())/sum(p_per_load.values()), sum(out_mwh_per_sgen.values())/sum(p_per_sgen.values())


def ict_double_failure(net, ict_net, needed_data):
    """
    Failure of two ict links simultaneously
    Both failures are repaired simultaneously
    """

    h_per_link = needed_data["h_per_link"]
    mttr_per_link = needed_data["mttr_per_link"]
    p_per_link = needed_data["p_per_link"]

    mg = needed_data["ict_graph"]
    failure_combinations = combinations(ict_net.link.index, 2)

    from_node_per_link = ict_net.link.from_node.to_dict()
    to_node_per_link = ict_net.link.to_node.to_dict()

    sgens_per_node = ict_net.client[ict_net.client.et=="sgen"].groupby("node").groups
    for key, val in sgens_per_node.items():
        sgens_per_node[key] = list(val)

    p_per_sgen = needed_data["p_per_sgen"]

    link_factor = needed_data["link_factor"]

    repair_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    out_mwh_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    unsupplied_per_combination = dict()
    for link1, link2 in failure_combinations:
        mg.remove_edges_from([(from_node_per_link[link1], to_node_per_link[link1]),
                              (from_node_per_link[link2], to_node_per_link[link2])])
        unsupplied = top.unsupplied_buses(net, mg, slacks=set(ict_net.server.node))

        h = (p_per_link[link1] * h_per_link[link2] + p_per_link[link2] * h_per_link[link1]) * 0.5
        for unsup_node in unsupplied:
            if unsup_node in sgens_per_node:
                for sgen in sgens_per_node[unsup_node]:
                    repair_time_per_sgen[sgen] += (mttr_per_link[link1] + mttr_per_link[link2]) * 0.5 * h
        unsupplied_per_combination[(link1, link2)] = unsupplied
        mg.add_edges_from([(from_node_per_link[link1], to_node_per_link[link1]),
                           (from_node_per_link[link2], to_node_per_link[link2])])

        link_factor[link1] -= h
        link_factor[link2] -= h

    for sgen in out_mwh_per_sgen.keys():
        out_mwh_per_sgen[sgen] = repair_time_per_sgen[sgen] / 60 * p_per_sgen[sgen]


    return sum(out_mwh_per_sgen.values())/sum(p_per_sgen.values())


def ps_double_failure(net, ict_net, needed_data):

    isolation_areas = needed_data["isolation_areas"]
    protection_areas = needed_data["protection_areas"]
    iso_area_data = needed_data["iso_area_data"]

    iso_areas_with_lines = needed_data["iso_areas_with_lines"]

    iso_time_per_load = {load: 0 for load in net.load.index}
    resup_time_per_load = {load: 0 for load in net.load.index}
    repair_time_per_load = {load: 0 for load in net.load.index}

    iso_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    resup_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    repair_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    total_outage_time_per_load = {load: 0 for load in net.load.index}
    p_per_load = needed_data["p_per_load"]
    out_mwh_per_load = {load: 0 for load in net.load.index}

    total_outage_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    p_per_sgen = needed_data["p_per_sgen"]
    out_mwh_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    cb_switches = needed_data["cb_switches"]
    open_switches = needed_data["open_switches"]
    ds_switches = needed_data["ds_switches"]

    h_per_line = needed_data["h_per_line"]
    mttr_per_line = needed_data["mttr_per_line"]

    switch_time_auto = needed_data["switch_time_auto"]
    switch_time_man = needed_data["switch_time_man"]

    supplied_switches = needed_data["supplied_switches"]
    supplied_sgens = needed_data["supplied_sgens"]

    t_loc = needed_data["t_loc"]
    t_rep = needed_data["t_rep"]

    loads_per_bus = needed_data["loads_per_bus"]
    sgens_per_bus = needed_data["sgens_per_bus"]

    line_factor = needed_data["line_factor"]


    iso_area_failure_combinations = combinations(iso_areas_with_lines, 2)

    iso_area_data_double = dict()

    for iso_area1, iso_area2 in iso_area_failure_combinations:
        iso1_protection_area_idx = isolation_areas[iso_area1]["protection_area"]
        iso2_protection_area_idx = isolation_areas[iso_area2]["protection_area"]

        iso1_protection_area_data = protection_areas[iso1_protection_area_idx]
        iso2_protection_area_data = protection_areas[iso2_protection_area_idx]

        if not set(chain.from_iterable(iso1_protection_area_data["resupply_areas"].values())) \
            & set(chain.from_iterable(iso2_protection_area_data["resupply_areas"].values())):
            continue

        direct_resupply_1 = iso1_protection_area_data["resupply_areas"].keys() - {iso1_protection_area_idx, iso2_protection_area_idx}
        direct_resupply_2 = iso2_protection_area_data["resupply_areas"].keys() - {iso1_protection_area_idx, iso2_protection_area_idx}

        line_combinations = list(product(isolation_areas[iso_area1]["lines"], isolation_areas[iso_area2]["lines"]))
        h = 0
        for line1, line2 in line_combinations:
            p_line1 = pi.P(h_per_line[line1], mttr_per_line[line1])
            p_line2 = pi.P(h_per_line[line2], mttr_per_line[line2])
            weight = (h_per_line[line1]*p_line2 + h_per_line[line2]*p_line1)*0.5

            line_factor[line1] -= weight
            line_factor[line2] -= weight

            h += weight

        data = dict()
        if direct_resupply_1 and direct_resupply_2:
            if iso1_protection_area_idx != iso2_protection_area_idx:
                data["resupplied_areas"] = iso_area_data[iso_area1]["resupplied_areas"] \
                                           + iso_area_data[iso_area2]["resupplied_areas"]
                data["resupplied_cb_areas"] = iso_area_data[iso_area1]["resupplied_cb_areas"] \
                                            + iso_area_data[iso_area2]["resupplied_cb_areas"]
                data["unsupplied_areas"] = iso_area_data[iso_area1]["unsupplied_areas"] \
                                           | iso_area_data[iso_area2]["unsupplied_areas"]
                data["resupply_switches"] = iso_area_data[iso_area1]["resupply_switches"] + \
                                            iso_area_data[iso_area2]["resupply_switches"]
                data["protection_switches"] = {iso_area_data[iso_area1]["protection_switch"],
                                               iso_area_data[iso_area2]["protection_switch"]}
                data["isolation_switches"] = [iso_area_data[iso_area1]["isolation_switches"],
                                              iso_area_data[iso_area2]["isolation_switches"]]
                iso_area_data_double[(iso_area1, iso_area2)] = data
            else:
                protection_switches = iso1_protection_area_data["protection_switches"]
                g = iso1_protection_area_data["iso_areas_graph"]

                resupply_areas = iso1_protection_area_data["resupply_areas"]
                resupply_switches = set()
                for res_area in resupply_areas.values():
                    resupply_switches.update(res_area)

                iso_areas_with_resupply_switch = set()
                iso_areas_with_protection_switch = set()
                resup_switches_per_iso_area = dict()
                for n, iso_area in isolation_areas.items():
                    if iso_area["protection_area"] != iso1_protection_area_idx:
                        continue
                    if iso_area["isolation_switches"] & resupply_switches:
                        iso_areas_with_resupply_switch.add(n)
                        resup_switches_per_iso_area[n] = iso_area["isolation_switches"] & resupply_switches
                    if iso_area["isolation_switches"] & protection_switches:
                        iso_areas_with_protection_switch.add(n)

                resupplied_areas = []
                resupplied_cb_areas = []
                unsupplied_areas = set()

                switches_of_resupplied_areas = []

                split_areas = top.connected_components(g, notravbuses={iso_area1, iso_area2})
                for area in split_areas:
                    area -= {iso_area1, iso_area2}
                    resupplied = False
                    if area & iso_areas_with_protection_switch:
                        resupplied_cb_areas.append(area)
                        resupplied = True
                    elif area & iso_areas_with_resupply_switch:
                        same_resupply_switch = False
                        resup_switches = set()
                        double_resup_switches = set()
                        if len(area & iso_areas_with_resupply_switch) > 1:
                            for a in area & iso_areas_with_resupply_switch:
                                resup_switch = resup_switches_per_iso_area[a]
                                if resup_switch & resup_switches:
                                    double_resup_switches.update(resup_switch & resup_switches)
                                resup_switches.update(resup_switch)
                            if not resup_switches - double_resup_switches:
                                same_resupply_switch = True
                        if not same_resupply_switch:
                            switches_of_resupplied_areas.append({switch_index(sw) for sw in resup_switches})
                            resupplied_areas.append(area)
                            resupplied = True
                    if not resupplied:
                        unsupplied_areas.update(area)
                    unsupplied_areas.update({iso_area1, iso_area2})

                    data["resupplied_areas"] = resupplied_areas
                    data["resupplied_cb_areas"] = resupplied_cb_areas
                    data["unsupplied_areas"] = unsupplied_areas
                    data["resupply_switches"] = switches_of_resupplied_areas
                    data["protection_switches"] = protection_switches
                    data["isolation_switches"] = isolation_areas[iso_area1]["isolation_switches"] \
                                                 | isolation_areas[iso_area2]["isolation_switches"]
                    iso_area_data_double[(iso_area1, iso_area2)] = data

        elif not direct_resupply_1 and not direct_resupply_2:
            # resupply through cb areas
            resupplied_cb_areas = set(chain.from_iterable(iso_area_data[iso_area1]["resupplied_cb_areas"])) \
                                  | set(chain.from_iterable(iso_area_data[iso_area2]["resupplied_cb_areas"]))

            possible_resupply_cb_switches = set(chain.from_iterable(iso1_protection_area_data["resupply_areas"].values())) \
                                            | set(chain.from_iterable(iso2_protection_area_data["resupply_areas"].values()))

            working_resupply_cb_switches = set()
            for area in resupplied_cb_areas:
                wrs = isolation_areas[area]["isolation_switches"] & possible_resupply_cb_switches
                if wrs:
                    working_resupply_cb_switches.update(wrs)

            resupply_areas = iso_area_data[iso_area1]["resupplied_areas"] \
                             + iso_area_data[iso_area2]["resupplied_areas"]

            resupplied_areas = []
            resupply_switches = []
            for res_areas in resupply_areas:
                for res_area in res_areas:
                    found_resupply_switches = isolation_areas[res_area]["isolation_switches"] \
                                                & working_resupply_cb_switches
                    if found_resupply_switches:
                        resupplied_areas.append(res_areas)
                        resupply_switches.append(found_resupply_switches)

            # resupply through resup areas
            resupplied_res_areas = set(chain.from_iterable(resupplied_areas))

            possible_resupply_switches = possible_resupply_cb_switches

            working_resupply_switches = set()
            for area in resupplied_res_areas:
                wrs = isolation_areas[area]["isolation_switches"] & possible_resupply_switches
                if wrs:
                    working_resupply_switches.update(wrs)

            resupply_areas = iso_area_data[iso_area1]["resupplied_areas"] \
                             + iso_area_data[iso_area2]["resupplied_areas"]

            for res_areas in resupply_areas:
                for res_area in res_areas:
                    found_resupply_switches = isolation_areas[res_area]["isolation_switches"] \
                                                & working_resupply_switches
                    if found_resupply_switches and not res_areas in resupplied_areas:
                        resupplied_areas.append(res_areas)
                        resupply_switches.append(found_resupply_switches)

            unsupplied_areas = (set(chain.from_iterable(iso_area_data[iso_area1]["resupplied_areas"])) \
                                | set(chain.from_iterable(iso_area_data[iso_area2]["resupplied_areas"]))) \
                                - set(chain.from_iterable(resupplied_areas))
            unsupplied_areas |= iso_area_data[iso_area1]["unsupplied_areas"] | iso_area_data[iso_area2]["unsupplied_areas"]

            data["resupplied_areas"] = resupplied_areas
            data["resupplied_cb_areas"] = iso_area_data[iso_area1]["resupplied_cb_areas"] +\
                                          iso_area_data[iso_area2]["resupplied_cb_areas"]
            data["unsupplied_areas"] = unsupplied_areas
            data["isolation_switches"] = iso_area_data[iso_area1]["isolation_switches"] \
                                         | iso_area_data[iso_area2]["isolation_switches"]
            data["resupply_switches"] = resupply_switches
            data["protection_switches"] = iso_area_data[iso_area1]["protection_switch"] \
                                          | iso_area_data[iso_area2]["protection_switch"]
            iso_area_data_double[(iso_area1, iso_area2)] = data
        else:
            direct_data = None
            indirect_data = None
            protection_area = None
            if direct_resupply_1:
                direct_data = iso_area_data[iso_area1]
                indirect_data = iso_area_data[iso_area2]
                direct_resupply = direct_resupply_1
                prot_area_data = iso1_protection_area_data
            elif direct_resupply_2:
                direct_data = iso_area_data[iso_area2]
                indirect_data = iso_area_data[iso_area1]
                direct_resupply = direct_resupply_2
                prot_area_data = iso2_protection_area_data

            possible_resupply_switches = set()
            for resup_areas in direct_data["resupplied_areas"]:
                for area in resup_areas:
                    resup_switches = {switch_index(switch) for switch in isolation_areas[area]["isolation_switches"]} \
                                   & set(chain.from_iterable(indirect_data["resupply_switches"]))
                    if resup_switches:
                        possible_resupply_switches.update(resup_switches)

            indirect_resupplied_areas = []
            indirect_resupply_switches = []
            indirect_unsupplied_areas = set()
            for res_area, res_sw in zip(indirect_data["resupplied_areas"], indirect_data["resupply_switches"]):
                    if res_sw & possible_resupply_switches:
                        indirect_resupplied_areas.append(res_area)
                        indirect_resupply_switches.append(res_sw & possible_resupply_switches)
                    else:
                        indirect_unsupplied_areas.update(res_area)

            all_direct_resupply_switches = {switch_index(sw) for sw in chain.from_iterable([prot_area_data["resupply_areas"][area] for area in direct_resupply])}

            data["resupplied_areas"] = direct_data["resupplied_areas"] + indirect_resupplied_areas
            data["unsupplied_areas"] = direct_data["unsupplied_areas"] | indirect_unsupplied_areas
            data["resupplied_cb_areas"] = direct_data["resupplied_cb_areas"] \
                                          + indirect_data["resupplied_cb_areas"]
            data["resupply_switches"] = [resup_sw & all_direct_resupply_switches
                                         for resup_sw in direct_data["resupply_switches"]] + indirect_resupply_switches
            data["protection_switches"] = [direct_data["protection_switch"], indirect_data["protection_switch"]]
            data["isolation_switches"] = direct_data["isolation_switches"] | indirect_data["isolation_switches"]
            iso_area_data_double[(iso_area1, iso_area2)] = data

        ##########################################

        # isolation time
        iso_switches_idxs = {switch_index(switch)
                             for switch in data["isolation_switches"]}
        iso_time = 0
        for switch in iso_switches_idxs - set(open_switches) - set(cb_switches):
            if switch in supplied_switches:
                iso_time += switch_time_auto[switch]
            else:
                iso_time += switch_time_man[switch]
        iso_time += t_loc
        iso_time *= h

        # repair time
        repair_time = t_rep *h

        # resupply time resupply_switches
        protection_switches = list()
        if isinstance(data["protection_switches"], int):
            data["protection_switches"] = {data["protection_switches"]}
        for switch in data["protection_switches"]:
            if isinstance(switch, int):
                protection_switches.append(switch)
            else:
                protection_switches.append(switch_index(switch))
        resup_time_cb = 0
        for switch in protection_switches:
            if switch in supplied_switches:
                resup_time_cb += switch_time_auto[switch]
            else:
                resup_time_cb += switch_time_man[switch]
        resup_time_cb *= h

        # resupply time protection switches
        resup_time = 0
        for switches in data["resupply_switches"]:
            if not switches:
                continue
            switch_times = []
            for switch in switches:
                if isinstance(switch, str):
                    switch = switch_index(switch)
                if switch in supplied_switches:
                    switch_times.append(switch_time_auto[switch])
                else:
                    switch_times.append(switch_time_man[switch])
            min_switch_time = min(switch_times)
            resup_time += min_switch_time
        resup_time *= h

        g1 = protection_areas[isolation_areas[iso_area1]["protection_area"]]["iso_areas_graph"]
        g2 = protection_areas[isolation_areas[iso_area2]["protection_area"]]["iso_areas_graph"]
        resupplied_areas = data["resupplied_areas"]
        resupplied_cb_areas = data["resupplied_cb_areas"]
        unsupplied_areas = data["unsupplied_areas"]

        # determine outage time per load
        for area_idx in set(g1.nodes()) | set(g2.nodes()):
            area = isolation_areas[area_idx]
            for bus in area["buses"]:
                loads = set(loads_per_bus[bus]) if bus in loads_per_bus else []
                sgens = set(sgens_per_bus[bus]) if bus in sgens_per_bus else []

                for load in loads:
                    if area_idx in set(chain.from_iterable(resupplied_areas)) \
                            | set(chain.from_iterable(resupplied_cb_areas)):
                        iso_time_per_load[load] += iso_time
                    if area_idx in unsupplied_areas:
                        repair_time_per_load[load] += repair_time
                    if area_idx in chain.from_iterable(resupplied_cb_areas):
                        resup_time_per_load[load] += resup_time_cb
                    if area_idx in chain.from_iterable(resupplied_areas):
                        resup_time_per_load[load] += resup_time

                for sgen in sgens:
                    if area_idx in set(chain.from_iterable(resupplied_areas)) \
                            | set(chain.from_iterable(resupplied_cb_areas)):
                        iso_time_per_sgen[sgen] += iso_time
                    if area_idx in unsupplied_areas or sgen not in supplied_sgens:
                        repair_time_per_sgen[sgen] += repair_time
                    if area_idx in chain.from_iterable(resupplied_cb_areas) and sgen in supplied_sgens:
                        resup_time_per_sgen[sgen] += resup_time_cb
                    if area_idx in chain.from_iterable(resupplied_areas) and sgen in supplied_sgens:
                        resup_time_per_sgen[sgen] += resup_time


    for load in total_outage_time_per_load.keys():
        total_outage_time_per_load[load] = (iso_time_per_load[load]
                                            + resup_time_per_load[load]
                                            + repair_time_per_load[load]) / 60
        out_mwh_per_load[load] = total_outage_time_per_load[load] * p_per_load[load]

    for sgen in total_outage_time_per_sgen.keys():
        total_outage_time_per_sgen[sgen] = (iso_time_per_sgen[sgen]
                                            + resup_time_per_sgen[sgen]
                                            + repair_time_per_sgen[sgen]) / 60
        out_mwh_per_sgen[sgen] = total_outage_time_per_sgen[sgen] * p_per_sgen[sgen]

    return sum(out_mwh_per_load.values())/sum(p_per_load.values()), sum(out_mwh_per_sgen.values())/sum(p_per_sgen.values())

    return iso_area_data_double


def ps_single_failure(net, ict_net, needed_data):

    switch_time_auto = needed_data["switch_time_auto"]#net.switch.time_auto_min.to_dict()
    switch_time_man = needed_data["switch_time_man"]#net.switch.time_auto_min.to_dict()

    supplied_switches = needed_data["supplied_switches"]
    supplied_sgens = needed_data["supplied_sgens"]

    isolation_areas = needed_data["isolation_areas"]
    protection_areas = needed_data["protection_areas"]
    iso_area_data = needed_data["iso_area_data"]

    h_per_line = needed_data["h_per_line"]
    line_factor = needed_data["line_factor"]

    h_per_iso_area = {area: sum(h_per_line[line] * line_factor[line]
                      for line in data["lines"]) for area, data in isolation_areas.items()}

    open_switches = needed_data["open_switches"]
    cb_switches = needed_data["cb_switches"]
    ds_switches = needed_data["ds_switches"]

    t_loc = needed_data["t_loc"]
    t_rep = needed_data["t_rep"]

    loads_per_bus = needed_data["loads_per_bus"]
    sgens_per_bus = needed_data["sgens_per_bus"]

    p_per_load = needed_data["p_per_load"]
    p_per_sgen = needed_data["p_per_sgen"]

    line_factor = needed_data["line_factor"]

    iso_time_per_load = {load: 0 for load in net.load.index}
    resup_time_per_load = {load: 0 for load in net.load.index}
    repair_time_per_load = {load: 0 for load in net.load.index}

    iso_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    resup_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    repair_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    total_outage_time_per_load = {load: 0 for load in net.load.index}
#    p_per_load = net.load.p_mw.to_dict()
    out_mwh_per_load = {load: 0 for load in net.load.index}

    total_outage_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
#    p_per_sgen = net.sgen.p_mw.to_dict()
    out_mwh_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    for iso_area, data in iso_area_data.items():
        ################################################################

        # h per isolation area
        h = h_per_iso_area[iso_area]

        # isolation time
        iso_switches_idxs = {switch_index(switch)
                             for switch in data["isolation_switches"]}
        iso_time = 0
        for switch in iso_switches_idxs - set(open_switches) - set(cb_switches):
            if switch in supplied_switches:
                iso_time += switch_time_auto[switch]
            else:
                iso_time += switch_time_man[switch]
        iso_time += t_loc
        iso_time *= h

        # repair time
        repair_time = t_rep *h

        # resupply time resupply_switches
        protection_sw = data["protection_switch"]
        resup_time_cb = switch_time_auto[protection_sw] if protection_sw in supplied_switches else switch_time_man[protection_sw]
        resup_time_cb *= h

        # resupply time protection switches
        resup_time = 0
        for switches in data["resupply_switches"]:
            switch_times = []
            for switch in switches:
                if switch in supplied_switches:
                    switch_times.append(switch_time_auto[switch])
                else:
                    switch_times.append(switch_time_man[switch])
            min_switch_time = min(switch_times)
            resup_time += min_switch_time
        resup_time *= h

        g = protection_areas[isolation_areas[iso_area]["protection_area"]]["iso_areas_graph"]
        resupplied_areas = data["resupplied_areas"]
        resupplied_cb_areas = data["resupplied_cb_areas"]
        unsupplied_areas = data["unsupplied_areas"]

        # determine outage time per load
        for area_idx in g.nodes():
            area = isolation_areas[area_idx]
            for bus in area["buses"]:
                loads = set(loads_per_bus[bus]) if bus in loads_per_bus else []
                sgens = set(sgens_per_bus[bus]) if bus in sgens_per_bus else []

                for load in loads:
                    if area_idx in set(chain.from_iterable(resupplied_areas)) \
                            | set(chain.from_iterable(resupplied_cb_areas)):
                        iso_time_per_load[load] += iso_time
                    if area_idx in unsupplied_areas:
                        repair_time_per_load[load] += repair_time
                    if area_idx in chain.from_iterable(resupplied_cb_areas):
                        resup_time_per_load[load] += resup_time_cb
                    if area_idx in chain.from_iterable(resupplied_areas):
                        resup_time_per_load[load] += resup_time

                for sgen in sgens:
                    if area_idx in set(chain.from_iterable(resupplied_areas)) \
                            | set(chain.from_iterable(resupplied_cb_areas)):
                        iso_time_per_sgen[sgen] += iso_time
                    if area_idx in unsupplied_areas or sgen not in supplied_sgens:
                        repair_time_per_sgen[sgen] += repair_time
                    if area_idx in chain.from_iterable(resupplied_cb_areas) and sgen in supplied_sgens:
                        resup_time_per_sgen[sgen] += resup_time_cb
                    if area_idx in chain.from_iterable(resupplied_areas) and sgen in supplied_sgens:
                        resup_time_per_sgen[sgen] += resup_time


    for load in total_outage_time_per_load.keys():
        total_outage_time_per_load[load] = (iso_time_per_load[load]
                                            + resup_time_per_load[load]
                                            + repair_time_per_load[load]) / 60
        out_mwh_per_load[load] = total_outage_time_per_load[load] * p_per_load[load]

    for sgen in total_outage_time_per_sgen.keys():
        total_outage_time_per_sgen[sgen] = (iso_time_per_sgen[sgen]
                                            + resup_time_per_sgen[sgen]
                                            + repair_time_per_sgen[sgen]) / 60
        out_mwh_per_sgen[sgen] = total_outage_time_per_sgen[sgen] * p_per_sgen[sgen]

    return sum(out_mwh_per_load.values())/sum(p_per_load.values()), sum(out_mwh_per_sgen.values())/sum(p_per_sgen.values())


def ict_single_failure(net, ict_net, needed_data):
    repair_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    required_links_per_client = needed_data["required_links_per_client"]
    h_per_link = needed_data["h_per_link"]
    mttr_per_link = needed_data["mttr_per_link"]

    sgen_clients = ict_net.client.index[ict_net.client.et=="sgen"]

    total_outage_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    p_per_sgen = needed_data["p_per_sgen"]
    out_mwh_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    link_factor = needed_data["link_factor"]

    failed_sgens_per_link = dict()
    for sgen_client in sgen_clients:
        if not sgen_client in required_links_per_client:
            continue

        for link in required_links_per_client[sgen_client]:
            if failed_sgens_per_link.get(link):
                failed_sgens_per_link[link].add(sgen_client)
            else:
                failed_sgens_per_link[link] = {sgen_client}

    for link, failed_sgens in failed_sgens_per_link.items():
        h = h_per_link[link] * link_factor[link]
        mttr = mttr_per_link[link]
        repair_time = mttr * h
        for failed_sgen in failed_sgens:
            repair_time_per_sgen[failed_sgen] += repair_time

    for sgen in repair_time_per_sgen.keys():
        total_outage_time_per_sgen[sgen] = repair_time_per_sgen[sgen] / 60
        out_mwh_per_sgen[sgen] = total_outage_time_per_sgen[sgen] * p_per_sgen[sgen]

    return sum(out_mwh_per_sgen.values())/sum(p_per_sgen.values())

def ict_double_failure(net, ict_net, needed_data):
    """
    Failure of two ict links simultaneously
    Both failures are repaired simultaneously
    """

    h_per_link = needed_data["h_per_link"]
    mttr_per_link = needed_data["mttr_per_link"]
    p_per_link = needed_data["p_per_link"]

    mg = needed_data["ict_graph"]
    failure_combinations = combinations(ict_net.link.index, 2)

    from_node_per_link = ict_net.link.from_node.to_dict()
    to_node_per_link = ict_net.link.to_node.to_dict()

    sgens_per_node = ict_net.client[ict_net.client.et=="sgen"].groupby("node").groups
    for key, val in sgens_per_node.items():
        sgens_per_node[key] = list(val)

    p_per_sgen = needed_data["p_per_sgen"]

    link_factor = needed_data["link_factor"]

    repair_time_per_sgen = {sgen: 0 for sgen in net.sgen.index}
    out_mwh_per_sgen = {sgen: 0 for sgen in net.sgen.index}

    unsupplied_per_combination = dict()
    for link1, link2 in failure_combinations:
        mg.remove_edges_from([(from_node_per_link[link1], to_node_per_link[link1]),
                              (from_node_per_link[link2], to_node_per_link[link2])])
        unsupplied = top.unsupplied_buses(net, mg, slacks=set(ict_net.server.node))

        h = (p_per_link[link1] * h_per_link[link2] + p_per_link[link2] * h_per_link[link1]) * 0.5
        for unsup_node in unsupplied:
            if unsup_node in sgens_per_node:
                for sgen in sgens_per_node[unsup_node]:
                    repair_time_per_sgen[sgen] += (mttr_per_link[link1] + mttr_per_link[link2]) * 0.5 * h
        unsupplied_per_combination[(link1, link2)] = unsupplied
        mg.add_edges_from([(from_node_per_link[link1], to_node_per_link[link1]),
                           (from_node_per_link[link2], to_node_per_link[link2])])

        link_factor[link1] -= h
        link_factor[link2] -= h

    for sgen in out_mwh_per_sgen.keys():
        out_mwh_per_sgen[sgen] = repair_time_per_sgen[sgen] / 60 * p_per_sgen[sgen]


    return sum(out_mwh_per_sgen.values())/sum(p_per_sgen.values())


def create_ict_network_for_simbench(net, mode="wired"):
    ict_net = pi.create_empty_ict_network()

    line_buses = set(net.line.from_bus) | set(net.line.to_bus)

    for i, bus in net.bus.iterrows():
        if i in line_buses:
            pi.create_ict_node(ict_net, index=i)

    server_node = pi.create_ict_node(ict_net)
    server = pi.create_ict_server(ict_net, server_node)

    if mode == "wired" or mode == "mixed":
        for i, line in net.line.iterrows():
            pi.create_ict_link(ict_net, line.from_bus, line.to_bus, length_km=line.length_km,
                               type="wired", in_service=False)
        pi.create_ict_link(ict_net, server_node, 2, length_km=0.1, type="wired", in_service=False)
        pi.create_ict_link(ict_net, server_node, 3, length_km=0.1, type="wired", in_service=False)
    if mode == "wireless" or mode == "mixed":
        buses_with_sgen_or_switch = set(net.sgen.bus) | set(net.switch.bus)
        for bus in buses_with_sgen_or_switch & line_buses:
            pi.create_ict_link(ict_net, server_node, bus, length_km=1, type="wireless",
                               in_service=False)

    for i, sgen in net.sgen.iterrows():
        pi.create_ict_client(ict_net, sgen.bus, element=i, et="sgen", server=server,
                             in_service=False)

    for i, switch in net.switch.iterrows():
        bus = switch.bus if switch.bus in line_buses else 2
        pi.create_ict_client(ict_net, bus, element=i, et="switch", server=server, in_service=False)

    return ict_net
