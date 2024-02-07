import pandapower as pp
import networks as nw
import pandaict_orig as pi
import numpy as np


def create_double_failure_test_network(meshed=False, ict_type="wired", all_edges_same_length=False):
    def get_edge_length(f, t, network):
        if isinstance(network, pp.pandapowerNet):
            net = network
            f_coords = np.array(net.bus_geodata.loc[f, ["x", "y"]])
            t_coords = np.array(net.bus_geodata.loc[t, ["x", "y"]])

            vec = f_coords - t_coords
            length_km = np.sqrt(sum(pow(vec, 2)))
            return length_km
        elif isinstance(network, pi.pandapowerIctNet):
            ict_net = network
            f_coords = np.array(ict_net.node_geodata.loc[f, ["x", "y"]])
            t_coords = np.array(ict_net.node_geodata.loc[t, ["x", "y"]])

            vec = f_coords - t_coords
            length_km = np.sqrt(sum(pow(vec, 2)))
            return length_km


    net = pp.create_empty_network()
    net.name = "double_failure_test_network"

    pp.create_buses(net, nr_buses=5, vn_kv=20)

    # geocoords
    net.bus_geodata.loc[0, ["x", "y"]] = (0, 0)
    net.bus_geodata.loc[1, ["x", "y"]] = (-1, 0)
    net.bus_geodata.loc[2, ["x", "y"]] = (-1, -1)
    net.bus_geodata.loc[3, ["x", "y"]] = (0, -2)
    net.bus_geodata.loc[4, ["x", "y"]] = (1, 0)

    net.line_geodata.loc[0] = [[(-1, 0), (-1, -1)]]
    net.line_geodata.loc[1] = [[(-1, -1), (-1, -2), (0, -2)]]
    net.line_geodata.loc[2] = [[(0, -2), (1, -2), (1, 0)]]

    for f, t in [(1, 2), (2, 3), (3, 4)]:
        length_km = 1 if all_edges_same_length else get_edge_length(f, t, net)
        pp.create_line(net, f, t, length_km=length_km, std_type="NAYY 4x50 SE")

    pp.create_ext_grid(net, 0)

    pp.create_load(net, bus=2, p_kw=10)
    pp.create_load(net, bus=3, p_kw=20)

    pp.create_switch(net, bus=0, element=1, et="b", type="CB")
    pp.create_switch(net, bus=0, element=4, et="b", type="CB")

    pp.create_switch(net, bus=1, element=0, et="l", type="LBS")
    pp.create_switch(net, bus=2, element=0, et="l", type="LBS")
    pp.create_switch(net, bus=2, element=1, et="l", type="LBS")
    pp.create_switch(net, bus=3, element=1, et="l", type="LBS")
    pp.create_switch(net, bus=3, element=2, et="l", type="LBS", closed=False)
    pp.create_switch(net, bus=4, element=2, et="l", type="LBS")


    net.switch["time_min"] = 20
    net.switch["time_manual_min"] = 20
    net.line["h_per_km"] = 0.06
    net.line["mttr"] = 10


    ict_net = pi.create_empty_ict_network()
#    ict_net.name = "create_double_failure_test_ict_network"

    for i in range(6):
        pi.create_ict_node(ict_net)

    # geocoords
    ict_net.node_geodata.loc[0, ["x", "y"]] = (-0.2, 0.1)
    ict_net.node_geodata.loc[1, ["x", "y"]] = (-0.2, -0.2)
    ict_net.node_geodata.loc[2, ["x", "y"]] = (-0.8, -0.2)
    ict_net.node_geodata.loc[3, ["x", "y"]] = (-0.8, -1)
    ict_net.node_geodata.loc[4, ["x", "y"]] = (0, -1.8)
    ict_net.node_geodata.loc[5, ["x", "y"]] = (0.8, -0.2)


    pi.create_ict_server(ict_net, 0)

    pi.create_ict_client(ict_net, node=1, server=0, element=0, et="switch")
    pi.create_ict_client(ict_net, node=1, server=0, element=1, et="switch")
    pi.create_ict_client(ict_net, node=2, server=0, element=2, et="switch")
    pi.create_ict_client(ict_net, node=3, server=0, element=3, et="switch")
    pi.create_ict_client(ict_net, node=3, server=0, element=4, et="switch")
    pi.create_ict_client(ict_net, node=4, server=0, element=5, et="switch")
    pi.create_ict_client(ict_net, node=4, server=0, element=6, et="switch")
    pi.create_ict_client(ict_net, node=5, server=0, element=7, et="switch")

    if ict_type == "wired" or ict_type == "mixed":
        geos = [[(-0.2, 0.1), (-0.2, -0.2)],
                [(-0.2, -0.2), (-0.8, -0.2)],
                [(-0.8, -0.2), (-0.8, -1)],
                [(-0.8, -1), (-0.8, -1.8), (0, -1.8)],
                [(-0.2, -0.2), (0.8, -0.2)]]

        for (f, t), geo in zip([(0, 1), (1, 2), (2, 3), (3, 4), (1, 5)], geos):
            length_km = 1 if all_edges_same_length else get_edge_length(f, t, ict_net)
            link = pi.create_ict_link(ict_net, f, t, length_km=length_km, type="wired")
            ict_net.link_geodata.loc[link] = [geo]

        if meshed:
            length_km = 1 if all_edges_same_length else get_edge_length(4, 5, ict_net)
            link = pi.create_ict_link(ict_net, 4, 5, length_km=length_km, type="wired")
            ict_net.link_geodata.loc[link] = [[(0, -1.8), (0.8, -0.2)]]

    if ict_type == "wireless" or ict_type == "mixed":
        server_node = ict_net.server.node.loc[0]
        server_coords = tuple(ict_net.node_geodata.loc[server_node, ["x", "y"]])
        wireless_links = []
        for node in set(ict_net.client.node):
            length_km = 1 if all_edges_same_length else get_edge_length(server_node, node, ict_net)
            link = pi.create_ict_link(ict_net, server_node, node, length_km=length_km, type="wireless")
            node_coords = tuple(ict_net.node_geodata.loc[node, ["x", "y"]])
            ict_net.link_geodata.loc[link] = [[server_coords, node_coords]]
            wireless_links.append(link)

        for link in wireless_links:
            from_node = ict_net.link.from_node.loc[link]
            to_node = ict_net.link.to_node.loc[link]

            from_node_antenna = ict_net.antenna[ict_net.antenna.node == from_node]
            if len(from_node_antenna) == 0:
                pi.create_ict_antenna(ict_net, from_node)

            to_node_antenna = ict_net.antenna[ict_net.antenna.node == to_node]
            if len(to_node_antenna) == 0:
                pi.create_ict_antenna(ict_net, to_node)


    ict_net.link["h_per_km"] = 0
    ict_net.link["mttr"] = 0
    ict_net.link["h_per_km"][ict_net.link.type=="wired"] = 0.02
    ict_net.link["mttr"][ict_net.link.type=="wired"] = 4
    ict_net.link["h_per_km"][ict_net.link.type=="wireless"] = 0.05
    ict_net.link["mttr"][ict_net.link.type=="wireless"] = 2

    return net, ict_net


def create_simbench_rural_with_ict(ict_type="meshed"):
    net = nw.simbench_mv_grid("rural", version=2)
    net = pp.from_json("D:\\Workspace\\Projekte\\ENSURE\\Netzdaten\\simbench_rural_with_geodata.json")

    ext_grid_bus = net.ext_grid.bus.values[0]
    switch_buses = net.switch.index[(net.switch.et=="l") | (net.switch.type == "CB")]

    ict_net = pi.create_empty_ict_network()

#    server_node = pi.create_ict_node(ict_net, index=max(net.bus.index)+1)

    for bus in net.bus.index:
        pi.create_ict_node(ict_net, index=bus)

    server_node=0
    server = pi.create_ict_server(ict_net, node=server_node)

    for node in ict_net.node.index:
        if node in net.bus_geodata.index:
            bus_coords = net.bus_geodata.loc[node]
            ict_net.node_geodata.loc[node] = np.array(bus_coords) + 3

    if ict_type=="meshed":
        for i, line in net.line.iterrows():
            pi.create_ict_link(ict_net, from_node=line.from_bus, to_node=line.to_bus,
                               length_km=line.length_km, type="wired")
    elif ict_type=="radial":
        open_lines = net.switch.element[(net.switch.et=="l") & (net.switch.closed==False)].values
#        print(open_lines)
        for i, line in net.line.iterrows():
            if i not in open_lines:
                pi.create_ict_link(ict_net, from_node=line.from_bus, to_node=line.to_bus,
                                   length_km=line.length_km, type="wired")


    pi.create_ict_link(ict_net, from_node=0, to_node=1, length_km=1, type="wired")
    pi.create_ict_link(ict_net, from_node=0, to_node=2, length_km=1, type="wired")

    switches = net.switch[(net.switch.et=="l") | (net.switch.type=="CB")]
    for i, switch in switches.iterrows():
        pi.create_ict_client(ict_net, switch.bus, server, et="switch", element=i)

    net.switch["time_min"] = 20
    net.switch["time_manual_min"] = 20
    net.line["h_per_km"] = 0.03
    net.line["mttr"] = 10

    ict_net.link["h_per_km"] = 0
    ict_net.link["mttr"] = 0
    ict_net.link["h_per_km"][ict_net.link.type=="wired"] = 0.02
    ict_net.link["mttr"][ict_net.link.type=="wired"] = 4
    ict_net.link["h_per_km"][ict_net.link.type=="wireless"] = 0.05
    ict_net.link["mttr"][ict_net.link.type=="wireless"] = 2

    return net, ict_net
