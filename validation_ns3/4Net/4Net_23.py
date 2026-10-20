import pandaict as pi
import pandaict.diagnosis
from pandaict.topology.routing import *
from pandaict.utils.enums import *

# // *********************************
# //        Network Topology
# //
# //               TCP
# //  App_A <----------------> App_B
# //   |                         |
# //   |            n1 ---1--- dev_B
# //   |           /  \
# //   |        2 /    \ 3
# //   |         /      \
# //  dev_A -0- n0 --6-- n2
# //             \      /
# //            5 \    / 4
# //               \  /
# //                n3
# //
# // *********************************

# set simulation parameters
link_type_01 = 'UMTS'
link_type_12 = 'Fiber'
link_type_02 = 'UMTS'
link_type_03 = 'Fiber'
link_type_23 = 'Fiber'
protocol = 'TCP'        # 20 Byte Packet Size
frequency = 1           # ms

# declare network
net = pi.create_empty_network("4n-Net")

# declare nodes
n0 = pi.create_ict_node(net, name="n0", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_02, link_type_23, link_type_03])
n1 = pi.create_ict_node(net, name="n1", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_02, link_type_23, link_type_03])
n2 = pi.create_ict_node(net, name="n2", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_02, link_type_23, link_type_03])
n3 = pi.create_ict_node(net, name="n3", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_02, link_type_23, link_type_03])

# declare devices
d0 = pi.create_ict_device(net, name='d0', device_type=DeviceType.SERVER)
d1 = pi.create_ict_device(net, name='d1', device_type=DeviceType.SERVER)

# connect devices to their respective nodes
link0 = pi.create_ict_link(net, name='link0', link_type='LAN1000', from_elt=d0, to_elt=[n0])
link1 = pi.create_ict_link(net, name='link1', link_type='LAN1000', from_elt=n1, to_elt=[d1])

# connect nodes
link01 = pi.create_ict_link(net, name='link02', link_type=link_type_01, from_elt=n0, to_elt=[n1])
link12 = pi.create_ict_link(net, name='link12', link_type=link_type_12, from_elt=n1, to_elt=[n2])
link23 = pi.create_ict_link(net, name='link23', link_type=link_type_23, from_elt=n2, to_elt=[n3])
link03 = pi.create_ict_link(net, name='link23', link_type=link_type_23, from_elt=n3, to_elt=[n0])
link02 = pi.create_ict_link(net, name='link12', link_type=link_type_02, from_elt=n0, to_elt=[n2])

# install apps
app0 = pi.create_ict_app(net, name='appA', app_type=AppType.CLIENT, device=d0)
app1 = pi.create_ict_app(net, name='appB', app_type=AppType.WEBSERVER, device=d1)

# set up connection
Connection_AB = pi.create_ict_connection(
    net,
    name='Connection_AB',
    from_app=app0,
    to_app=app1,
    protocol=protocol,
    info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
    peers=(app0, app1),
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


