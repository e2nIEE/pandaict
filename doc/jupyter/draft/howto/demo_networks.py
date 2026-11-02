import pandaict as pi
from pandaict.utils.enums import NodeType, DeviceType, AppType

def simple_net(mtbf_h_n=0, mttr_h_n=0, mtbf_h_l=8760, mttr_h_l=0):
    # =============================================
    # simple_net
    #
    # {app_a}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{app_b}
    #   |                                   |
    # [Alice] --- (node_a) --- (node_b) --- [Bob]
    #
    # []=dev, ()=node, {}=app
    # =============================================

    net = pi.create_empty_network('simple_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': mtbf_h_l, 'mttr_h': mttr_h_l},
                       name='ETH', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=mtbf_h_n, mttr_h=mttr_h_n)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=mtbf_h_n, mttr_h=mttr_h_n)

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net, name='link_ab', from_elt=node_a, to_elt=node_b, link_type='ETH')

    pi.create_ict_link(net, name='link_a', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net, name='link_b', from_elt=dev_b, to_elt=node_b, link_type='ETH_perfect')

    return net, app_a, app_b

def simple_multi_net():
    # ===========================================================
    # simple_multi_net
    #
    # {app_a}~~~~~~~~~~~~~~~~~~~{app_b}~~~~~~~~~~~~~~~~~~~{app_c}
    #   |                        |                        |
    # [Alice] --- (node_ab) --- [Bob] --- (node_bc) --- [Charlie]
    #
    # []=dev, ()=node, {}=app,  ---=link
    # ===========================================================

    net = pi.create_empty_network('simple_multi_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    node_ab = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=0, mttr_h=0)
    node_bc = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=0, mttr_h=0)

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)
    dev_c = pi.create_ict_device(net, name='Charlie', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)
    app_c = pi.create_ict_app(net, name='Charlie', app_type=AppType.WEBSERVER, device=dev_c)

    pi.create_ict_link(net, name='link_a', from_elt=dev_a, to_elt=node_ab, link_type='ETH_perfect')
    pi.create_ict_link(net, name='link_b1', from_elt=node_ab, to_elt=dev_b, link_type='ETH_perfect')
    pi.create_ict_link(net, name='link_b2', from_elt=dev_b, to_elt=node_bc, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=node_bc, to_elt=dev_c, link_type='ETH_perfect')

    return net, app_a, app_b, app_c


def two_source_parallel_net(mtbf_h=8760, mttr_h=24):
    # ===========================================================
    # two_source_parallel_net
    #
    # Two independent paths from different sources to one target.
    # This demonstrates basic redundancy where either source can
    # communicate with the target independently.
    #
    #              [NodeA]----[NodeB]----+
    #            /                        \
    # [Alice]---+                          +---[NodeE]---[Bob]
    #            \                        /
    #              [NodeC]----[NodeD]----+
    #
    # Connections:
    #   Path 1: Alice -> NodeA -> NodeB -> NodeE -> Bob
    #   Path 2: Alice -> NodeC -> NodeD -> NodeE -> Bob
    #
    # min_connected=-1: Both paths required (series logic)
    # min_connected=1:  Either path suffices (parallel logic)
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('two_source_parallel_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 8760, 'mttr_h': 24},
                       name='ETH', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    node_c = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    node_d = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    node_e = pi.create_ict_node(net, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    
    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)
    
    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkC', from_elt=dev_a, to_elt=node_c, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=node_a, to_elt=node_b, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkBE', from_elt=node_b, to_elt=node_e, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkCD', from_elt=node_c, to_elt=node_d, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkDE', from_elt=node_d, to_elt=node_e, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkB', from_elt=node_e, to_elt=dev_b, link_type='ETH_perfect')

    return net, app_a, app_b


def two_source_shared_component_net(mttr_h=0):
    # ===========================================================
    # two_source_shared_component_net
    #
    # Two paths from different sources to one target, sharing a common
    # node in the middle. This demonstrates how shared components
    # become critical bottlenecks.
    #
    #  [Alice]   --- (NodeA) --- +                  + --- (NodeB) --- [Bob]
    #                            |                  |
    #                            + --- (Shared) --- +
    #                            |                  |
    #  [Charlie] --- (NodeC) --- +                  + --- (NodeD) --- [Diana]
    #
    # Connections:
    #   Path 1: Alice -> NodeA -> SharedNode -> NodeB -> Bob
    #   Path 2: Alice -> NodeC -> SharedNode -> Bob
    #
    # Note: SharedNode is on BOTH paths, making it a single point of failure
    #
    # []=dev, ()=node, {}=app
    # ===========================================================
    """
    Returns
    -------
    net, [appAlice, appCharlie], [appBob, appDiana]
    """
    net = pi.create_empty_network(name='net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'], 'mtbf_h': 0, 'mttr_h': 0},
                        name='ETH_perfect', element='link', overwrite=False, check_required=True)

    n_a = pi.create_ict_node(net, name="NodeA", mtbf_h=8760, mttr_h=mttr_h)
    n_b = pi.create_ict_node(net, name="NodeB", mtbf_h=8760, mttr_h=mttr_h)
    n_c = pi.create_ict_node(net, name="NodeC", mtbf_h=8760, mttr_h=mttr_h)
    n_d = pi.create_ict_node(net, name="NodeD", mtbf_h=8760, mttr_h=mttr_h)
    n_s = pi.create_ict_node(net, name="Shared", mtbf_h=8760, mttr_h=mttr_h)

    # Pair 1 path: NodeA - Shared - NodeB
    pi.create_ict_link(net, from_elt=n_a, to_elt=n_s, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=n_s, to_elt=n_b, link_type='ETH_perfect')

    # Pair 2 path: NodeC ─ Shared ─ NodeD
    pi.create_ict_link(net, from_elt=n_c, to_elt=n_s, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=n_s, to_elt=n_d, link_type='ETH_perfect')

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)
    dev_c = pi.create_ict_device(net, name='Charlie', device_type=DeviceType.SERVER)
    dev_d = pi.create_ict_device(net, name='Diana', device_type=DeviceType.SERVER)

    pi.create_ict_link(net, from_elt=dev_a, to_elt=n_a, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=dev_b, to_elt=n_b, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=dev_c, to_elt=n_c, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=dev_d, to_elt=n_d, link_type='ETH_perfect')

    app_a = pi.create_ict_app(net, name="Alice", app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name="Bob", app_type=AppType.CLIENT, device=dev_b)
    app_c = pi.create_ict_app(net, name="Charlie", app_type=AppType.CLIENT, device=dev_c)
    app_d = pi.create_ict_app(net, name="Diana", app_type=AppType.CLIENT, device=dev_d)

    return net, [app_a, app_c], [app_b, app_d]


def four_path_net():
    # ===========================================================
    # four_path_net
    #
    # 2 sources x 2 targets = 4 independent paths.
    # In order to realize the 4 independent connections virtual devices have to be installed
    # Demonstrates broadcasting: when sources and targets have
    # different lengths, they are broadcast to match.
    #
    #              (vdev1)---[NodeA]----[NodeB]----+
    #             /                                 \
    # [Source1]--+                                   +---[NodeC]---[Target1]
    #            \                                  /
    #              (vdev2)---[NodeD]----[NodeE]----+
    #
    #               (vdev3)---[NodeF]----[NodeG]---+
    #               /                               \
    #   [Source2]--+                                 +---[NodeH]---[Target2]
    #               \                               /
    #               (vdev4)---[NodeI]----[NodeJ]---+
    #
    # Connections (broadcasting):
    #   vdev1 -> Target1
    #   vdev2 -> Target1
    #   vdev3 -> Target2
    #   vdev4 -> Target2
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('four_path_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 8760, 'mttr_h': 24},
                       name='ETH', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    node_c = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    node_d = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    node_e = pi.create_ict_node(net, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)

    node_f = pi.create_ict_node(net, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    node_g = pi.create_ict_node(net, name='NodeG', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    node_h = pi.create_ict_node(net, name='NodeH', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    node_i = pi.create_ict_node(net, name='NodeI', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    node_j = pi.create_ict_node(net, name='NodeJ', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)

    vdev1 = pi.create_ict_device(net, name='vdev1', device_type=DeviceType.SERVER)
    vdev2 = pi.create_ict_device(net, name='vdev2', device_type=DeviceType.SERVER)
    vdev3 = pi.create_ict_device(net, name='vdev3', device_type=DeviceType.SERVER)
    vdev4 = pi.create_ict_device(net, name='vdev4', device_type=DeviceType.SERVER)

    dev_t1 = pi.create_ict_device(net, name='Target1', device_type=DeviceType.SERVER)
    dev_t2 = pi.create_ict_device(net, name='Target2', device_type=DeviceType.SERVER)

    app_v1 = pi.create_ict_app(net, name='app_v1', app_type=AppType.CLIENT, device=vdev1)
    app_v2 = pi.create_ict_app(net, name='app_v2', app_type=AppType.CLIENT, device=vdev2)
    app_v3 = pi.create_ict_app(net, name='app_v3', app_type=AppType.CLIENT, device=vdev3)
    app_v4 = pi.create_ict_app(net, name='app_v4', app_type=AppType.CLIENT, device=vdev4)

    app_t1 = pi.create_ict_app(net, name='Target1', app_type=AppType.WEBSERVER, device=dev_t1)
    app_t2 = pi.create_ict_app(net, name='Target2', app_type=AppType.WEBSERVER, device=dev_t2)

    pi.create_ict_link(net, name='linkS1A', from_elt=vdev1, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS2D', from_elt=vdev2, to_elt=node_d, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS1F', from_elt=vdev3, to_elt=node_f, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS2I', from_elt=vdev4, to_elt=node_i, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkAB', from_elt=node_a, to_elt=node_b, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkBC', from_elt=node_b, to_elt=node_c, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkCD', from_elt=node_c, to_elt=node_e, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkDE', from_elt=node_d, to_elt=node_e, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkFG', from_elt=node_f, to_elt=node_g, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkGH', from_elt=node_g, to_elt=node_h, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkHI', from_elt=node_h, to_elt=node_j, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkIJ', from_elt=node_i, to_elt=node_j, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkCT1', from_elt=node_c, to_elt=dev_t1, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkJT2', from_elt=node_h, to_elt=dev_t2, link_type='ETH_perfect')

    return net, [app_v1, app_v2, app_v3, app_v4], [app_t1, app_t1, app_t2, app_t2]


def heterogeneous_rate_net():
    # ===========================================================
    # heterogeneous_rate_net
    #
    # Network with components having DIFFERENT failure rates.
    # This demonstrates the difference between rate_adjustment=True
    # and rate_adjustment=False.
    #
    # Components with varying MTBF:
    #   - node_a: MTBF = 1000h (high failure rate)
    #   - node_b: MTBF = 10000h (medium failure rate)
    #   - node_c: MTBF = 50000h (low failure rate, reliable)
    #
    # Topology (simple chain):
    #   [Alice] -- node_a -- node_b -- node_c -- [Bob]
    #
    # With rate_adjustment=True:  Normalizes by expected failure rates
    #   -> Identifies TOPOLOGICAL bottlenecks (structural importance)
    #   -> All nodes are equally critical structurally (all on single path)
    #
    # With rate_adjustment=False: Raw failure frequencies
    #   -> Shows which components CAUSE failures most often
    #   -> node_a appears most critical because it fails most frequently
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('heterogeneous_rate_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER,
                               mtbf_h=1000, mttr_h=8)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER,
                               mtbf_h=10000, mttr_h=8)
    node_c = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER,
                               mtbf_h=50000, mttr_h=8)

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=node_a, to_elt=node_b, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkBC', from_elt=node_b, to_elt=node_c, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=node_c, to_elt=dev_b, link_type='ETH_perfect')

    return net, app_a, app_b


def simple_serial_chain_net():
    # ===========================================================
    # simple_serial_chain_net
    #
    # Simple 4-node serial chain for demonstrating serial criticality.
    # All components are equally critical structurally - each is a
    # single point of failure.
    #
    # Topology:
    #   [Alice] -- NodeA -- NodeB -- NodeC -- NodeD -- [Bob]
    #
    # With rate_adjustment=True: All nodes have score ~1.0
    # With rate_adjustment=False: All nodes have same raw frequency
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('simple_serial_chain_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 8760, 'mttr_h': 24},
                       name='ETH_failable', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_c = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_d = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=node_a, to_elt=node_b, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkBC', from_elt=node_b, to_elt=node_c, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkCD', from_elt=node_c, to_elt=node_d, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=node_d, to_elt=dev_b, link_type='ETH_perfect')

    return net, app_a, app_b


def parallel_with_backbone_net():
    # ===========================================================
    # parallel_with_backbone_net
    #
    # Network with parallel paths that share a common backbone.
    # This demonstrates how shared (backbone) components become
    # more critical than unique (parallel) components.
    #
    # Topology:
    #                     [NodeC]----[NodeD]
    #                    /                  \
    # [Alice]---[NodeA]-+                    +---[NodeE]---[Bob]
    #                    \                  /
    #                     [NodeB]----[NodeF]
    #
    # Backbone (shared): NodeA, NodeE
    # Parallel (unique): NodeB, NodeC, NodeD, NodeF
    #
    # Expected with rate_adjustment=True:
    #   - Backbone nodes (NodeA, NodeE): HIGHER scores (>1)
    #   - Parallel nodes (NodeB, NodeC, NodeD, NodeF): LOWER scores (<1)
    #
    # Expected with rate_adjustment=False:
    #   - All nodes: Same frequency (same MTBF)
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('parallel_with_backbone_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 8760, 'mttr_h': 24},
                       name='ETH', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_c = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_d = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_e = pi.create_ict_node(net, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_f = pi.create_ict_node(net, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkAB', from_elt=node_a, to_elt=node_b, link_type='ETH')
    pi.create_ict_link(net, name='linkAC', from_elt=node_a, to_elt=node_c, link_type='ETH')

    pi.create_ict_link(net, name='linkBD', from_elt=node_b, to_elt=node_d, link_type='ETH')
    pi.create_ict_link(net, name='linkCF', from_elt=node_c, to_elt=node_f, link_type='ETH')

    pi.create_ict_link(net, name='linkDE', from_elt=node_d, to_elt=node_e, link_type='ETH')
    pi.create_ict_link(net, name='linkFE', from_elt=node_f, to_elt=node_e, link_type='ETH')

    pi.create_ict_link(net, name='linkB', from_elt=node_e, to_elt=dev_b, link_type='ETH_perfect')

    return net, app_a, app_b


def single_component_net():
    # ===========================================================
    # single_component_net
    #
    # Simple network with ONE fail-able component.
    # Used to demonstrate PURE EXPONENTIAL reliability function.
    #
    # Topology:
    #   [Alice] -- NodeA -- [Bob]
    #
    # The reliability function R(t) = exp(-t/MTBF) for this case.
    # This is a pure exponential distribution.
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('single_component_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 8760, 'mttr_h': 0},  # Non-repairable
                       name='ETH_failable', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)  # Non-repairable

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=node_a, to_elt=dev_b, link_type='ETH_perfect')

    return net, app_a, app_b


def series_two_component_net():
    # ===========================================================
    # series_two_component_net
    #
    # Two fail-able components in SERIES.
    # Still produces EXPONENTIAL reliability function.
    #
    # Topology:
    #   [Alice] -- NodeA -- NodeB -- [Bob]
    #
    # The reliability function R(t) = exp(-2*t/MTBF) for this case.
    # This is still exponential (sum of exponentials in series).
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('series_two_component_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 8760, 'mttr_h': 0},  # Non-repairable
                       name='ETH_failable', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=node_a, to_elt=node_b, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=node_b, to_elt=dev_b, link_type='ETH_perfect')

    return net, app_a, app_b


def parallel_redundant_net():
    # ===========================================================
    # parallel_redundant_net
    #
    # Two fail-able components in parallel (redundancy).
    # This produces a non-exponential reliability function!
    #
    # Topology:
    #   [Alice] -- NodeA --+
    #                      +-- [Bob]
    #            -- NodeB --+
    #
    # Note: NodeA and NodeB are in parallel - either can provide
    # the connection. The system only fails if BOTH fail.
    #
    # The reliability function:
    #   R(t) = 1 - (1 - exp(-t/MTBF))^2
    #
    # This is NOT a pure exponential - it's a quadratic in exp(-t/MTBF).
    # The curve will be HIGHER than exponential for small t (due to redundancy)
    # and converge toward zero for large t.
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('parallel_redundant_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 8760, 'mttr_h': 0},  # Non-repairable
                       name='ETH_failable', element='link', overwrite=False, check_required=True)

    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=dev_a, to_elt=node_b, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkA2', from_elt=node_a, to_elt=dev_b, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB2', from_elt=node_b, to_elt=dev_b, link_type='ETH_perfect')

    return net, app_a, app_b


def triangle_net(mtbf_h, mttr_h):
    net = pi.create_empty_network('example_net')

    # create custom link type to avoid unexpected behavior
    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_A', element='link', overwrite=False, check_required=True)

    # create nodes
    node_a = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    node_b = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    node_c = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)

    # create devices
    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    # install apps on devices
    app_a = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    # connect nodes
    pi.create_ict_link(net, name='link_ab', from_elt=node_a, to_elt=node_b, link_type='ETH_A')
    pi.create_ict_link(net, name='link_ac', from_elt=node_a, to_elt=node_c, link_type='ETH_A')
    pi.create_ict_link(net, name='link_bc', from_elt=node_b, to_elt=node_c, link_type='ETH_A')

    # connect devices to nodes
    pi.create_ict_link(net, name='link_a', from_elt=dev_a, to_elt=node_a, link_type='ETH_A')
    pi.create_ict_link(net, name='link_b', from_elt=dev_b, to_elt=node_b, link_type='ETH_A')

    return net, app_a, app_b


def net_hardened():
    # Create hardened network
    net_hardened = pi.create_empty_network('hardened_net')

    pi.create_std_type(net_hardened, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                                      'protocols': ['TCP'],
                                      'mtbf_h': 8760, 'mttr_h': 24},
                       name='ETH', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net_hardened, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                                      'protocols': ['TCP'],
                                      'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    # NodeA and NodeE are HARDENED (10x more reliable)
    node_a = pi.create_ict_node(net_hardened, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    node_b = pi.create_ict_node(net_hardened, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_c = pi.create_ict_node(net_hardened, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_d = pi.create_ict_node(net_hardened, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_e = pi.create_ict_node(net_hardened, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    node_f = pi.create_ict_node(net_hardened, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    dev_a = pi.create_ict_device(net_hardened, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net_hardened, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net_hardened, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net_hardened, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net_hardened, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net_hardened, name='linkAB', from_elt=node_a, to_elt=node_b, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkAC', from_elt=node_a, to_elt=node_c, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkBD', from_elt=node_b, to_elt=node_d, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkCF', from_elt=node_c, to_elt=node_f, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkDE', from_elt=node_d, to_elt=node_e, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkFE', from_elt=node_f, to_elt=node_e, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkB', from_elt=node_e, to_elt=dev_b, link_type='ETH_perfect')

    return net_hardened, app_a, app_b

def net_parallel_hardened():
    # Create network where we harden the parallel nodes instead
    net_parallel_hardened = pi.create_empty_network('parallel_hardened_net')

    pi.create_std_type(net_parallel_hardened, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                                               'protocols': ['TCP'],
                                               'mtbf_h': 8760, 'mttr_h': 24},
                       name='ETH', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net_parallel_hardened, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                                               'protocols': ['TCP'],
                                               'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    # NodeA and NodeE stay NORMAL, NodeB, NodeC, NodeD, NodeF are HARDENED
    node_a = pi.create_ict_node(net_parallel_hardened, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_b = pi.create_ict_node(net_parallel_hardened, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    node_c = pi.create_ict_node(net_parallel_hardened, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    node_d = pi.create_ict_node(net_parallel_hardened, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    node_e = pi.create_ict_node(net_parallel_hardened, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    node_f = pi.create_ict_node(net_parallel_hardened, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)

    dev_a = pi.create_ict_device(net_parallel_hardened, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net_parallel_hardened, name='Bob', device_type=DeviceType.SERVER)

    app_a = pi.create_ict_app(net_parallel_hardened, name='Alice', app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net_parallel_hardened, name='Bob', app_type=AppType.WEBSERVER, device=dev_b)

    pi.create_ict_link(net_parallel_hardened, name='linkA', from_elt=dev_a, to_elt=node_a, link_type='ETH_perfect')
    pi.create_ict_link(net_parallel_hardened, name='linkAB', from_elt=node_a, to_elt=node_b, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkAC', from_elt=node_a, to_elt=node_c, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkBD', from_elt=node_b, to_elt=node_d, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkCF', from_elt=node_c, to_elt=node_f, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkDE', from_elt=node_d, to_elt=node_e, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkFE', from_elt=node_f, to_elt=node_e, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkB', from_elt=node_e, to_elt=dev_b, link_type='ETH_perfect')

    return net_parallel_hardened, app_a, app_b

def tutorial_net():
    return None


def large_net():
    return None


def simple_repairable_net(mttr_h=24):
    """
    Two nodes in series with configurable repair time. Perfect links.

    Topology
    --------
        [Alice] ---- (NodeA) ---- (NodeB) ---- [Bob]
        Nodes : mtbf_h = 8 760 h, mttr_h = <param>
        Link  : perfect (never fails)

    Returns
    -------
    net, appAlice, appBob
    """
    net = pi.create_empty_network(name='simple_repairable_net')
    n1 = pi.create_ict_node(net, name="NodeA", type="generic_node",
                            mtbf_h=8760, mttr_h=mttr_h)
    n2 = pi.create_ict_node(net, name="NodeB", type="generic_node",
                            mtbf_h=8760, mttr_h=mttr_h)
    pi.create_ict_link(net, from_node=n1, to_node=n2, type="perfect_link")
    app_a = pi.create_ict_app(net, name="Alice", node=n1, type="generic_app")
    app_b = pi.create_ict_app(net, name="Bob",   node=n2, type="generic_app")
    return net, app_a, app_b


def simple_two_pair_net(mttr_h=0):
    """
    Two fully independent node-pairs (no shared components). Perfect links.

    Topology
    --------
        Pair 1: [Alice]   ---- (NodeA) ---- (NodeB) ---- [Bob]
        Pair 2: [Charlie] ---- (NodeC) ---- (NodeD) ---- [Diana]
        (no connection between the two pairs)

    Returns
    -------
    net, [appAlice, appCharlie], [appBob, appDiana]
    """
    net = pi.create_empty_network(name='simple_two_pair_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                                               'protocols': ['TCP'],
                                               'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    n_a = pi.create_ict_node(net, name="NodeA", mtbf_h=8760, mttr_h=mttr_h)
    n_b = pi.create_ict_node(net, name="NodeB", mtbf_h=8760, mttr_h=mttr_h)
    n_c = pi.create_ict_node(net, name="NodeC", mtbf_h=8760, mttr_h=mttr_h)
    n_d = pi.create_ict_node(net, name="NodeD", mtbf_h=8760, mttr_h=mttr_h)

    pi.create_ict_link(net, from_elt=n_a, to_elt=n_b, link_type="ETH_perfect")
    pi.create_ict_link(net, from_elt=n_c, to_elt=n_d, link_type="ETH_perfect")

    dev_a = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    dev_b = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    pi.create_ict_link(net, from_elt=dev_a, to_elt=n_a, link_type="ETH_perfect")
    pi.create_ict_link(net, from_elt=n_b, to_elt=dev_b, link_type="ETH_perfect")

    dev_c = pi.create_ict_device(net, name='Charlie', device_type=DeviceType.SERVER)
    dev_d = pi.create_ict_device(net, name='Diana', device_type=DeviceType.SERVER)

    pi.create_ict_link(net, from_elt=dev_c, to_elt=n_c, link_type="ETH_perfect")
    pi.create_ict_link(net, from_elt=n_d, to_elt=dev_d, link_type="ETH_perfect")

    app_a = pi.create_ict_app(net, name="Alice", app_type=AppType.CLIENT, device=dev_a)
    app_b = pi.create_ict_app(net, name="Bob", app_type=AppType.CLIENT, device=dev_b)
    app_c = pi.create_ict_app(net, name="Charlie", app_type=AppType.CLIENT, device=dev_c)
    app_d = pi.create_ict_app(net, name="Diana", app_type=AppType.CLIENT, device=dev_d)

    return net, [app_a, app_c], [app_b, app_d]
