import pandaict as pi
from pandaict.utils.enums import *

def simple_net():
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
                             'mtbf_h': 8760, 'mttr_h': 0},
                       name='ETH', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER)

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

    return net


def two_source_parallel_net():
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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeD = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeE = pi.create_ict_node(net, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkC', from_elt=devA, to_elt=nodeC, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH')
    pi.create_ict_link(net, name='linkBE', from_elt=nodeB, to_elt=nodeE, link_type='ETH')

    pi.create_ict_link(net, name='linkCD', from_elt=nodeC, to_elt=nodeD, link_type='ETH')
    pi.create_ict_link(net, name='linkDE', from_elt=nodeD, to_elt=nodeE, link_type='ETH')

    pi.create_ict_link(net, name='linkB', from_elt=nodeE, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB


def two_source_shared_component_net():
    # ===========================================================
    # two_source_shared_component_net
    #
    # Two paths from different sources to one target, sharing a common
    # node in the middle. This demonstrates how shared components
    # become critical bottlenecks.
    #
    #              [NodeA]----[SharedNode]----[NodeB]----+
    #            /                                          \
    # [Alice]---+                                            +---[Bob]
    #            \                                          /
    #              [NodeC]--------------------------------+
    #
    # Connections:
    #   Path 1: Alice -> NodeA -> SharedNode -> NodeB -> Bob
    #   Path 2: Alice -> NodeC -> SharedNode -> Bob
    #
    # Note: SharedNode is on BOTH paths, making it a single point of failure
    #
    # []=dev, ()=node, {}=app
    # ===========================================================

    net = pi.create_empty_network('two_source_shared_component_net')

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 8760, 'mttr_h': 24},
                       name='ETH', element='link', overwrite=False, check_required=True)

    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                             'protocols': ['TCP'],
                             'mtbf_h': 0, 'mttr_h': 0},
                       name='ETH_perfect', element='link', overwrite=False, check_required=True)

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    sharedNode = pi.create_ict_node(net, name='SharedNode', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    devA = pi.create_ict_device(net, name='Alice', device_type=DeviceType.SERVER)
    devB = pi.create_ict_device(net, name='Bob', device_type=DeviceType.SERVER)

    appA = pi.create_ict_app(net, name='Alice', app_type=AppType.CLIENT, device=devA)
    appB = pi.create_ict_app(net, name='Bob', app_type=AppType.WEBSERVER, device=devB)

    pi.create_ict_link(net, name='linkA', from_elt=devA, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkC', from_elt=devA, to_elt=nodeC, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkAShared', from_elt=nodeA, to_elt=sharedNode, link_type='ETH')
    pi.create_ict_link(net, name='linkCShared', from_elt=nodeC, to_elt=sharedNode, link_type='ETH')

    pi.create_ict_link(net, name='linkSharedB', from_elt=sharedNode, to_elt=nodeB, link_type='ETH')

    pi.create_ict_link(net, name='linkB', from_elt=nodeB, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB, sharedNode


def four_path_net():
    # ===========================================================
    # four_path_net
    #
    # 2 sources x 2 targets = 4 independent paths.
    # Demonstrates broadcasting: when sources and targets have
    # different lengths, they are broadcast to match.
    #
    #              [NodeA]----[NodeB]----+
    #            /                          \
    # [Source1]--+                            +---[NodeC]---[Target1]
    #            \                          /
    #              [NodeD]----[NodeE]----+
    #
    #              [NodeF]----[NodeG]----+
    #            /                          \
    # [Source2]--+                            +---[NodeH]---[Target2]
    #            \                          /
    #              [NodeI]----[NodeJ]----+
    #
    # Connections (broadcasting):
    #   Source1 -> Target1
    #   Source2 -> Target2
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

    nodeA = pi.create_ict_node(net, name='NodeA', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeB = pi.create_ict_node(net, name='NodeB', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeC = pi.create_ict_node(net, name='NodeC', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeD = pi.create_ict_node(net, name='NodeD', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeE = pi.create_ict_node(net, name='NodeE', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    nodeF = pi.create_ict_node(net, name='NodeF', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeG = pi.create_ict_node(net, name='NodeG', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeH = pi.create_ict_node(net, name='NodeH', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeI = pi.create_ict_node(net, name='NodeI', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)
    nodeJ = pi.create_ict_node(net, name='NodeJ', node_type=NodeType.ROUTER, mtbf_h=8760, mttr_h=24)

    devS1 = pi.create_ict_device(net, name='Source1', device_type=DeviceType.SERVER)
    devS2 = pi.create_ict_device(net, name='Source2', device_type=DeviceType.SERVER)
    devT1 = pi.create_ict_device(net, name='Target1', device_type=DeviceType.SERVER)
    devT2 = pi.create_ict_device(net, name='Target2', device_type=DeviceType.SERVER)

    appS1 = pi.create_ict_app(net, name='Source1', app_type=AppType.CLIENT, device=devS1)
    appS2 = pi.create_ict_app(net, name='Source2', app_type=AppType.CLIENT, device=devS2)
    appT1 = pi.create_ict_app(net, name='Target1', app_type=AppType.WEBSERVER, device=devT1)
    appT2 = pi.create_ict_app(net, name='Target2', app_type=AppType.WEBSERVER, device=devT2)

    pi.create_ict_link(net, name='linkS1A', from_elt=devS1, to_elt=nodeA, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS1F', from_elt=devS1, to_elt=nodeF, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS2D', from_elt=devS2, to_elt=nodeD, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkS2I', from_elt=devS2, to_elt=nodeI, link_type='ETH_perfect')

    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH')
    pi.create_ict_link(net, name='linkBC', from_elt=nodeB, to_elt=nodeC, link_type='ETH')
    pi.create_ict_link(net, name='linkCD', from_elt=nodeC, to_elt=nodeD, link_type='ETH')
    pi.create_ict_link(net, name='linkDE', from_elt=nodeD, to_elt=nodeE, link_type='ETH')

    pi.create_ict_link(net, name='linkFG', from_elt=nodeF, to_elt=nodeG, link_type='ETH')
    pi.create_ict_link(net, name='linkGH', from_elt=nodeG, to_elt=nodeH, link_type='ETH')
    pi.create_ict_link(net, name='linkHI', from_elt=nodeH, to_elt=nodeI, link_type='ETH')
    pi.create_ict_link(net, name='linkIJ', from_elt=nodeI, to_elt=nodeJ, link_type='ETH')

    pi.create_ict_link(net, name='linkCT1', from_elt=nodeE, to_elt=devT1, link_type='ETH_perfect')
    pi.create_ict_link(net, name='linkJT2', from_elt=nodeJ, to_elt=devT2, link_type='ETH_perfect')

    return net, [appS1, appS2], [appT1, appT2]


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

    return net, appA, appB, [nodeA, nodeB, nodeC]


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
    pi.create_ict_link(net, name='linkAB', from_elt=nodeA, to_elt=nodeB, link_type='ETH_failable')
    pi.create_ict_link(net, name='linkBC', from_elt=nodeB, to_elt=nodeC, link_type='ETH_failable')
    pi.create_ict_link(net, name='linkCD', from_elt=nodeC, to_elt=nodeD, link_type='ETH_failable')
    pi.create_ict_link(net, name='linkB', from_elt=nodeD, to_elt=devB, link_type='ETH_perfect')

    return net, appA, appB, [nodeA, nodeB, nodeC, nodeD]


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

    return net, appA, appB, {'backbone': [nodeA, nodeE], 'parallel': [nodeB, nodeC, nodeD, nodeF]}


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

    return net, appA, appB, nodeA


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

    return net, appA, appB, [nodeA, nodeB]


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

    return net, appA, appB, [nodeA, nodeB]


def tutorial_net():
    return None


def large_net():
    return None
