import networkx


def create_ict_graph(ict_net, protocol="all"):
    mg = networkx.MultiGraph()
    mg.add_edges_from(
            (fb, tb, {"weight": float(l), "key": int(idx)})
            for fb, tb, l, protocols, idx, in_service in
            zip(ict_net.link.from_node,
                ict_net.link.to_node,
                ict_net.link.length_km,
                ict_net.link.protocols,
                ict_net.link.index,
                ict_net.link.in_service)
            if in_service and (protocol == "all" or protocol in protocols)
            )
    unused_nodes = set(mg.nodes) - {node for edge in mg.edges for node in edge}
    oos_nodes = set(ict_net.node.index[~ict_net.node.in_service])
    mg.remove_nodes_from(unused_nodes | oos_nodes)
    return mg


