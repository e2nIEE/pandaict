import pandaict as pi
import pandaict.diagnosis
from pandaict.plot import create_plot
from pandaict.topology.routing import *
from pandaict.utils.enums import *

# // *********************************
# //        Network Topology
# //
# //                TCP
# // App_A <-----------------> App_B
# //   |                        |
# //   |     0      2      1    |
# //  dev_A --- n1 --- n2 --- dev_B
# //             \     /
# //            4 \   / 3
# //               \ /
# //                n3
# //
# // *********************************

# set simulation parameters
link_type_AB = 'UMTS'
link_type_AC = 'Fiber'
link_type_BC = 'Fiber'
protocol = 'TCP'        # 20 Byte Packet Size
frequency = 1           # ms


# declare network
net = pi.create_empty_network("3Net")

# declare nodes
nodeA = pi.create_ict_node(net, name="nodeA", node_type=NodeType.ROUTER, link_types=[link_type_AB, link_type_AC, link_type_BC])
nodeB = pi.create_ict_node(net, name="nodeB", node_type=NodeType.ROUTER, link_types=[link_type_AB, link_type_AC, link_type_BC])
nodeC = pi.create_ict_node(net, name="nodeC", node_type=NodeType.ROUTER, link_types=[link_type_AB, link_type_AC, link_type_BC])

devA = pi.create_ict_device(net, name='devA', device_type=DeviceType.SERVER)
devB = pi.create_ict_device(net, name='devB', device_type=DeviceType.SERVER)

# Connect Devices to their respective nodes
linkA = pi.create_ict_link(net, name='linkA', link_type='LAN1000', from_elt=nodeA, to_elt=[devA])
linkB = pi.create_ict_link(net, name='linkB', link_type='LAN1000', from_elt=nodeB, to_elt=[devB])

# Connect Nodes
linkAB = pi.create_ict_link(net, name='linkAB', link_type=link_type_AB, from_elt=nodeA, to_elt=[nodeB])
linkBC = pi.create_ict_link(net, name='linkBC', link_type=link_type_BC, from_elt=nodeB, to_elt=[nodeC])
linkAC = pi.create_ict_link(net, name='linkAC', link_type=link_type_AC, from_elt=nodeA, to_elt=[nodeC])

appA = pi.create_ict_app(net, name='appA', app_type=AppType.CLIENT, device=devA)
appB = pi.create_ict_app(net, name='appB', app_type=AppType.WEBSERVER, device=devB)

Connection_AB = pi.create_ict_connection(
    net,
    name='Connection_AB',
    from_app=appA,
    to_app=appB,
    protocol=protocol,
    info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
    peers=(appA, appB),
    producer=[0,1],
    prod_freq_ms=[frequency, -1]
)

pandaict.diagnosis.inspect(net)

print('\n-------- ROUTES FOR CONNECTION --------')
print(calc_routes_for_connection(net, Connection_AB))

lup = calc_lup_table(net, Connection_AB, routing_type=RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True)

print('\n-------- CONNECTION BANDWIDTH --------')
print(calc_conn_bandwidth_Mbps(net, Connection_AB))

print('\n-------- LINKS FOR CONNECTION --------')
print(calc_sorted_links_by_connection(net, Connection_AB, routing_type=RoutingType.LOWEST_TOTAL_LATENCY))

print('\n-------- LINK BANDWIDTH --------')
print(calc_link_bandwidth_Mbps(net, lup))


