import pandaict_orig as pi
from pandaict.outage.ict_toolbox import (
    get_unsupplied_nodes, get_isolation_and_protection_areas, get_isolation_area_data,
    ps_ict_failure, ict_double_failure, ps_double_failure, ps_single_failure, ict_single_failure
)


def reliability_ps_ict(net, ict_net, t_loc=75, t_rep=600):
    needed_data = dict()

    # supplied clients
    ict_graph = pi.topology.create_ict_graph(ict_net)
    needed_data["ict_graph"] = ict_graph

    unsupp_nodes = get_unsupplied_nodes(
        ict_graph, set(ict_net.server.node.values))
    supplied_nodes = set(ict_net.node.index) - unsupp_nodes

    supplied_sgens = set(ict_net.client.element[
        (ict_net.client.et == "sgen") & (
            ict_net.client.node.isin(supplied_nodes))
    ])
    supplied_switches = set(ict_net.client.element[
        (ict_net.client.et == "switch") & (
            ict_net.client.node.isin(supplied_nodes))
    ])
    needed_data["supplied_sgens"] = supplied_sgens
    needed_data["supplied_switches"] = supplied_switches

    # switches
    cb_switches = net.switch.index[net.switch.type == "CB"]
    open_switches = net.switch.index[(
        net.switch.closed == False) & (net.switch.type == "LBS")]
    ds_switches = net.switch.index[net.switch.type == "DS"]
    needed_data["cb_switches"] = cb_switches
    needed_data["open_switches"] = open_switches
    needed_data["ds_switches"] = ds_switches

    # determine isolation and protection areas
    isolation_areas, protection_areas = get_isolation_and_protection_areas(net, open_switches,
                                                                           cb_switches, ds_switches)
    iso_area_data = get_isolation_area_data(isolation_areas, protection_areas)
    needed_data["isolation_areas"] = isolation_areas
    needed_data["protection_areas"] = protection_areas
    needed_data["iso_area_data"] = iso_area_data

    # weighting factors
    line_factor = {line: 1 for line in net.line.index}
    link_factor = {link: 1 for link in ict_net.link.index}
    needed_data["line_factor"] = line_factor
    needed_data["link_factor"] = link_factor

    # ict links and clients
    required_links_per_client, required_links = pi.get_required_links_per_client(
        ict_net)
    iso_areas_with_lines = {iso_area for iso_area,
                            data in isolation_areas.items() if data["lines"]}
    needed_data["required_links_per_client"] = required_links_per_client
    needed_data["required_links"] = required_links
    needed_data["iso_areas_with_lines"] = iso_areas_with_lines

    client_per_sgen = ict_net.client[ict_net.client.et == "sgen"].groupby(
        "element").groups
    for key, val in client_per_sgen.items():
        client_per_sgen[key] = list(val)
    needed_data["client_per_sgen"] = client_per_sgen

    client_per_switch = ict_net.client[ict_net.client.et == "switch"].groupby(
        "element").groups
    for key, val in client_per_switch.items():
        client_per_switch[key] = list(val)
    needed_data["client_per_switch"] = client_per_switch

    # loads and sgens
    loads_per_bus = net.load.groupby("bus").groups
    for key, val in loads_per_bus.items():
        loads_per_bus[key] = list(val)
    needed_data["loads_per_bus"] = loads_per_bus

    sgens_per_bus = net.sgen.groupby("bus").groups
    for key, val in sgens_per_bus.items():
        sgens_per_bus[key] = list(val)
    needed_data["sgens_per_bus"] = sgens_per_bus

    p_per_sgen = net.sgen.p_mw.to_dict()
    p_per_load = net.load.p_mw.to_dict()
    needed_data["p_per_load"] = p_per_load
    needed_data["p_per_sgen"] = p_per_sgen

    # hazard rates
    h_per_line = (net.line.h_per_km*net.line.length_km).to_dict()
    h_per_link = (ict_net.link.h_per_km * ict_net.link.length_km).to_dict()
    needed_data["h_per_line"] = h_per_line
    needed_data["h_per_link"] = h_per_link

    mttr_per_line = net.line.mttr.to_dict()
    mttr_per_link = ict_net.link.mttr.to_dict()
    needed_data["mttr_per_line"] = mttr_per_line
    needed_data["mttr_per_link"] = mttr_per_link

    p_per_link = {link: pi.P(
        h_per_link[link], mttr_per_link[link]) for link in ict_net.link.index}
    needed_data["p_per_link"] = p_per_link

    switch_time_man = net.switch.time_man_min.to_dict()
    switch_time_auto = net.switch.time_auto_min.to_dict()
    needed_data["switch_time_man"] = switch_time_man
    needed_data["switch_time_auto"] = switch_time_auto

    needed_data["t_loc"] = t_loc
    needed_data["t_rep"] = t_rep

    # asidi of power and ict system failures
    asidi_ps_ict_load, asidi_ps_ict_sgen = ps_ict_failure(
        net, ict_net, needed_data)  # isolation_areas,
#                                                          iso_area_data, line_factor, link_factor)
    asidi_ict_ict_sgen = ict_double_failure(net, ict_net, needed_data)
    asidi_ps_ps_load, asidi_ps_ps_sgen = ps_double_failure(
        net, ict_net, needed_data)
    asidi_ps_load, asidi_ps_sgen = ps_single_failure(net, ict_net, needed_data)
    asidi_ict_sgen = ict_single_failure(net, ict_net, needed_data)

    asidi_load = asidi_ps_ict_load + asidi_ps_ps_load + asidi_ps_load
    asidi_sgen = asidi_ps_ict_sgen + asidi_ps_ps_sgen + asidi_ps_sgen + asidi_ict_ict_sgen \
        + asidi_ict_sgen

#    print("PS ICT")
#    print(asidi_ps_ict_load, asidi_ps_ict_sgen)
#    print("ICT ICT")
#    print(asidi_ict_ict_sgen)
#    print("PS PS")
#    print(asidi_ps_ps_load, asidi_ps_ps_sgen)
#    print("PS")
#    print(asidi_ps_load, asidi_ps_sgen)
#    print("ICT")
#    print(asidi_ict_sgen)
#
#    plot_asidis(asidi_ps_ict_load, asidi_ps_ict_sgen, asidi_ict_ict_sgen, asidi_ps_ps_load,
#        asidi_ps_ps_sgen, asidi_ps_load, asidi_ps_sgen, asidi_ict_sgen)

    return asidi_load * 60, asidi_sgen * 60


if __name__ == "__main__":
    import simbench
    from pandaict.outage.ict_toolbox import create_ict_network_for_simbench

    #net = simbench.get_simbench_net("1-MV-comm--0-sw")
    net = simbench.get_simbench_net("1-MV-rural--0-sw")
    ict_net = create_ict_network_for_simbench(net, "wired")
    #net = simbench.get_simbench_net("1-MV-semiurb--0-sw")
    #net = pp.from_json("simplified_mv_rural.json")
    #net = nw.mv_network("ring")
    #net = nw.mv_network("triple")
    #net = nw.mv_network("mixed")
    #net = nw.mv_oberrhein()
#    net, ict_net = create_networks()
    #net = nw.case9241pegase()
    #open_ds_switches = net.switch.index[(net.switch.type=="DS") & (~net.switch.closed)]
    #net.switch.drop(open_ds_switches, inplace=True)
    #net.switch.type[net.switch.bus.isin([8, 10])] = "LBS"
    net.line["h_per_km"] = 0.03
    net.line["mttr"] = 600
    net.switch["time_man_min"] = 20
    net.switch["time_auto_min"] = 0
#    #net.switch.time_min[net.switch.type == "CB"] = 0
#    #
    ict_net.link["h_per_km"] = 0.02
    ict_net.link["mttr"] = 120
#
    ict_net.link.in_service = True
    ict_net.client.in_service = True

    asidi_load, asidi_sgen = reliability_ps_ict(net, ict_net)
