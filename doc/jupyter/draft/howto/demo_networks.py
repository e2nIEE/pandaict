import pandaict as pi
from pandaict.utils.enums import *

def simple_net(mtbf_h_n=0, mttr_h_n=0, mtbf_h_l=8760, mttr_h_l=0):
    # =============================================
    # simple_net
    #
    # {appA}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~{appB}
    #   |                                   |
    # [Alice] --- (nodeA) --- (nodeB) --- [Bob]
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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=mtbf_h_n, mttr_h=mttr_h_n)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=mtbf_h_n, mttr_h=mttr_h_n)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    linkAB = pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH')

    linkA = pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    linkB = pi.create_ict_link(net, name='linkB', from_elt=devB, to_elt=nodeB, link_type='ETH_perfect')

    return net, appA, appB

def simple_multi_net():
    # ===========================================================
    # simple_multi_net
    #
    # {appA}~~~~~~~~~~~~~~~~~~~{appB}~~~~~~~~~~~~~~~~~~~{appC}
    #   |                        |                        |
    # [Alice] --- (nodeAB) --- [Bob] --- (nodeBC) --- [Charlie]
    #
    # []=dev, ()=node, {}=app,  ---=link
    # ===========================================================

    net = pi.create_empty_network('simple_multi_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    nodeAB = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=0, mttr_h=0)
    nodeBC = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=0, mttr_h=0)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)
    devC = pi.create_ict_device(net, name='Charlie', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)
    appC = pi.create_ict_app(net, name='Charlie', app_type=AppType.WEBSERVER, device=devC)

    linkA = pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeAB, link_type='ETH_perfect')
    linkB1 = pi.create_ict_link(net, name='linkB1', from_elt=nodeAB, to_elt=devB, link_type='ETH_perfect')
    linkB2 = pi.create_ict_link(net, name='linkB2', from_elt=devB, to_elt=nodeBC, link_type='ETH_perfect')
    linkC = pi.create_ict_link(net, name='linkB', from_elt=nodeBC, to_elt=devC, link_type='ETH_perfect')

    return net, appA, appB, appC


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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    nodeD = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    nodeE = pi.create_ict_node(net, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkC', from_elt=devA, to_elt=nodeC, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkBE', from_elt=nodeB, to_elt=nodeE, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkCD', from_elt=nodeC, to_elt=nodeD, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkDE', from_elt=nodeD, to_elt=nodeE, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkB', from_elt=nodeE, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB


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

    nA = pi.create_ict_node(net, name="NodeA", mtbf_h=8760, mttr_h=mttr_h)
    nB = pi.create_ict_node(net, name="NodeB", mtbf_h=8760, mttr_h=mttr_h)
    nC = pi.create_ict_node(net, name="NodeC", mtbf_h=8760, mttr_h=mttr_h)
    nD = pi.create_ict_node(net, name="NodeD", mtbf_h=8760, mttr_h=mttr_h)
    nS = pi.create_ict_node(net, name="Shared", mtbf_h=8760, mttr_h=mttr_h)

    # Pair 1 path: NodeA - Shared - NodeB
    pi.create_ict_link(net, from_elt=nA, to_elt=nS, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=nS, to_elt=nB, link_type='ETH_perfect')

    # Pair 2 path: NodeC ─ Shared ─ NodeD
    pi.create_ict_link(net, from_elt=nC, to_elt=nS, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=nS, to_elt=nD, link_type='ETH_perfect')

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)
    devC = pi.create_ict_device(net, name='Charlie', device_type=DeviceType.SERVER)
    devD = pi.create_ict_device(net, name='Diana', device_type=DeviceType.SERVER)

    pi.create_ict_link(net, from_elt=devA, to_elt=nA, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=devB, to_elt=nB, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=devC, to_elt=nC, link_type='ETH_perfect')
    pi.create_ict_link(net, from_elt=devD, to_elt=nD, link_type='ETH_perfect')

    appA = pi.create_ict_app(net, name="Alice", app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name="Bob", app_type=AppType.CLIENT, device=devB)
    appC = pi.create_ict_app(net, name="Charlie", app_type=AppType.CLIENT, device=devC)
    appD = pi.create_ict_app(net, name="Diana", app_type=AppType.CLIENT, device=devD)

    return net, [appA, appC], [appB, appD]


def four_path_net():
    # ===========================================================
    # four_path_net
    #
    # 2 sources x 2 targets = 4 independent paths.
    # In order to realize the 4 independent connections virtual devices have to be installed
    # Demonstrates broadcasting: when sources and targets have
    # different lengths, they are broadcast to match.
    #
    #              (Vdev1)---[NodeA]----[NodeB]----+
    #             /                                 \
    # [Source1]--+                                   +---[NodeC]---[Target1]
    #            \                                  /
    #              (Vdev2)---[NodeD]----[NodeE]----+
    #
    #               (Vdev3)---[NodeF]----[NodeG]---+
    #               /                               \
    #   [Source2]--+                                 +---[NodeH]---[Target2]
    #               \                               /
    #               (Vdev4)---[NodeI]----[NodeJ]---+
    #
    # Connections (broadcasting):
    #   Vdev1 -> Target1
    #   Vdev2 -> Target1
    #   Vdev3 -> Target2
    #   Vdev4 -> Target2
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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    nodeD = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    nodeE = pi.create_ict_node(net, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)

    nodeF = pi.create_ict_node(net, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    nodeG = pi.create_ict_node(net, name='NodeG', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    nodeH = pi.create_ict_node(net, name='NodeH', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    nodeI = pi.create_ict_node(net, name='NodeI', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)
    nodeJ = pi.create_ict_node(net, name='NodeJ', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=0)

    Vdev1 = pi.create_ict_device(net, name='Vdev1', device_type=DeviceType.SERVER)
    Vdev2 = pi.create_ict_device(net, name='Vdev2', device_type=DeviceType.SERVER)
    Vdev3 = pi.create_ict_device(net, name='Vdev3', device_type=DeviceType.SERVER)
    Vdev4 = pi.create_ict_device(net, name='Vdev4', device_type=DeviceType.SERVER)

    devT1 = pi.create_ict_device(net, name='Target1', device_type=DeviceType.SERVER)
    devT2 = pi.create_ict_device(net, name='Target2', device_type=DeviceType.SERVER)

    appV1 = pi.create_ict_app(net, name='appV1', app_type=AppType.CLIENT, device=Vdev1)
    appV2 = pi.create_ict_app(net, name='appV2', app_type=AppType.CLIENT, device=Vdev2)
    appV3 = pi.create_ict_app(net, name='appV3', app_type=AppType.CLIENT, device=Vdev3)
    appV4 = pi.create_ict_app(net, name='appV4', app_type=AppType.CLIENT, device=Vdev4)

    appT1 = pi.create_ict_app(net, name='Target1', app_type=AppType.WEBSERVER, device=devT1)
    appT2 = pi.create_ict_app(net, name='Target2', app_type=AppType.WEBSERVER, device=devT2)

    pi.create_ict_link(net, name='linkS1A', from_elt=Vdev1, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS2D', from_elt=Vdev2, to_elt=nodeD, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS1F', from_elt=Vdev3, to_elt=nodeF, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS2I', from_elt=Vdev4, to_elt=nodeI, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkBC', from_elt=nodeB, to_elt=nodeC, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkCD', from_elt=nodeC, to_elt=nodeE, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkDE', from_elt=nodeD, to_elt=nodeE, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkFG', from_elt=nodeF, to_elt=nodeG, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkGH', from_elt=nodeG, to_elt=nodeH, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkHI', from_elt=nodeH, to_elt=nodeJ, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkIJ', from_elt=nodeI, to_elt=nodeJ, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkCT1', from_elt=nodeC, to_elt=devT1, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkJT2', from_elt=nodeH, to_elt=devT2, link_type='ETH_perfect')

    return net, [appV1, appV2, appV3, appV4], [appT1, appT1, appT2, appT2]


def heterogeneous_rate_net():
    # ===========================================================
    # heterogeneous_rate_net
    #
    # Network with components having DIFFERENT failure rates.
    # This demonstrates the difference between rate_adjustment=True
    # and rate_adjustment=False.
    #
    # Components with varying MTBF:
    #   - nodeA: MTBF = 1000h (high failure rate)
    #   - nodeB: MTBF = 10000h (medium failure rate)
    #   - nodeC: MTBF = 50000h (low failure rate, reliable)
    #
    # Topology (simple chain):
    #   [Alice] -- nodeA -- nodeB -- nodeC -- [Bob]
    #
    # With rate_adjustment=True:  Normalizes by expected failure rates
    #   -> Identifies TOPOLOGICAL bottlenecks (structural importance)
    #   -> All nodes are equally critical structurally (all on single path)
    #
    # With rate_adjustment=False: Raw failure frequencies
    #   -> Shows which components CAUSE failures most often
    #   -> nodeA appears most critical because it fails most frequently
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('heterogeneous_rate_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER,
                               mtbf_h=1000, mttr_h=8)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER,
                               mtbf_h=10000, mttr_h=8)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER,
                               mtbf_h=50000, mttr_h=8)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkBC', from_elt=nodeB, to_elt=nodeC, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=nodeC, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB


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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeD = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkBC', from_elt=nodeB, to_elt=nodeC, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkCD', from_elt=nodeC, to_elt=nodeD, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=nodeD, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB


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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeD = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeE = pi.create_ict_node(net, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeF = pi.create_ict_node(net, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH')
    pi.create_ict_link(net, name='linkAC', from_elt=nodeA, to_elt=nodeC, link_type='ETH')

    pi.create_ict_link(net, name='linkBD', from_elt=nodeB, to_elt=nodeD, link_type='ETH')
    pi.create_ict_link(net, name='linkCF', from_elt=nodeC, to_elt=nodeF, link_type='ETH')

    pi.create_ict_link(net, name='linkDE', from_elt=nodeD, to_elt=nodeE, link_type='ETH')
    pi.create_ict_link(net, name='linkFE', from_elt=nodeF, to_elt=nodeE, link_type='ETH')

    pi.create_ict_link(net, name='linkB', from_elt=nodeE, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB


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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)  # Non-repairable

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB


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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=nodeB, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB


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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER,
                               mtbf_h=8760, mttr_h=0)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB', from_elt=devA, to_elt=nodeB, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkA2', from_elt=nodeA, to_elt=devB, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkB2', from_elt=nodeB, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB


def triangle_net(mtbf_h, mttr_h):
    net = pi.create_empty_network('example_net')

    # create custom link type to avoid unexpected behavior
    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_A', element='link', overwrite=False, check_required=True)

    # create nodes
    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=mtbf_h, mttr_h=mttr_h)

    # create devices
    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    # install apps on devices
    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    # connect nodes
    linkAB = pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH_A')
    linkAC = pi.create_ict_link(net, name='linkAC', from_elt=nodeA, to_elt=nodeC, link_type='ETH_A')
    linkBC = pi.create_ict_link(net, name='linkBC', from_elt=nodeB, to_elt=nodeC, link_type='ETH_A')

    # connect devices to nodes
    linkA = pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_A')
    linkB = pi.create_ict_link(net, name='linkB', from_elt=devB, to_elt=nodeB, link_type='ETH_A')

    return net, appA, appB


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
    nodeA = pi.create_ict_node(net_hardened, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    nodeB = pi.create_ict_node(net_hardened, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeC = pi.create_ict_node(net_hardened, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeD = pi.create_ict_node(net_hardened, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeE = pi.create_ict_node(net_hardened, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    nodeF = pi.create_ict_node(net_hardened, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    devA = pi.create_ict_device(net_hardened, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net_hardened, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net_hardened, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net_hardened, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net_hardened, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net_hardened, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkAC', from_elt=nodeA, to_elt=nodeC, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkBD', from_elt=nodeB, to_elt=nodeD, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkCF', from_elt=nodeC, to_elt=nodeF, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkDE', from_elt=nodeD, to_elt=nodeE, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkFE', from_elt=nodeF, to_elt=nodeE, link_type='ETH')
    pi.create_ict_link(net_hardened, name='linkB', from_elt=nodeE, to_elt=devB, link_type='ETH_perfect')

    return net_hardened, appA, appB

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
    nodeA = pi.create_ict_node(net_parallel_hardened, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeB = pi.create_ict_node(net_parallel_hardened, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    nodeC = pi.create_ict_node(net_parallel_hardened, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    nodeD = pi.create_ict_node(net_parallel_hardened, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)
    nodeE = pi.create_ict_node(net_parallel_hardened, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeF = pi.create_ict_node(net_parallel_hardened, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=87600, mttr_h=24)

    devA = pi.create_ict_device(net_parallel_hardened, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net_parallel_hardened, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net_parallel_hardened, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net_parallel_hardened, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net_parallel_hardened, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net_parallel_hardened, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkAC', from_elt=nodeA, to_elt=nodeC, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkBD', from_elt=nodeB, to_elt=nodeD, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkCF', from_elt=nodeC, to_elt=nodeF, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkDE', from_elt=nodeD, to_elt=nodeE, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkFE', from_elt=nodeF, to_elt=nodeE, link_type='ETH')
    pi.create_ict_link(net_parallel_hardened, name='linkB', from_elt=nodeE, to_elt=devB, link_type='ETH_perfect')

    return net_parallel_hardened, appA, appB

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
    appA = pi.create_ict_app(net, name="Alice", node=n1, type="generic_app")
    appB = pi.create_ict_app(net, name="Bob",   node=n2, type="generic_app")
    return net, appA, appB


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

    nA = pi.create_ict_node(net, name="NodeA", mtbf_h=8760, mttr_h=mttr_h)
    nB = pi.create_ict_node(net, name="NodeB", mtbf_h=8760, mttr_h=mttr_h)
    nC = pi.create_ict_node(net, name="NodeC", mtbf_h=8760, mttr_h=mttr_h)
    nD = pi.create_ict_node(net, name="NodeD", mtbf_h=8760, mttr_h=mttr_h)

    pi.create_ict_link(net, from_elt=nA, to_elt=nB, link_type="ETH_perfect")
    pi.create_ict_link(net, from_elt=nC, to_elt=nD, link_type="ETH_perfect")

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    pi.create_ict_link(net, from_elt=devA, to_elt=nA, link_type="ETH_perfect")
    pi.create_ict_link(net, from_elt=nB, to_elt=devB, link_type="ETH_perfect")

    devC = pi.create_ict_device(net, name='Charlie', device_type=DeviceType.SERVER)
    devD = pi.create_ict_device(net, name='Diana', device_type=DeviceType.SERVER)

    pi.create_ict_link(net, from_elt=devC, to_elt=nC, link_type="ETH_perfect")
    pi.create_ict_link(net, from_elt=nD, to_elt=devD, link_type="ETH_perfect")

    appA = pi.create_ict_app(net, name="Alice", app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name="Bob", app_type=AppType.CLIENT, device=devB)
    appC = pi.create_ict_app(net, name="Charlie", app_type=AppType.CLIENT, device=devC)
    appD = pi.create_ict_app(net, name="Diana", app_type=AppType.CLIENT, device=devD)

    return net, [appA, appC], [appB, appD]
