import pandaict as pi
import pandaict.diagnosis
from pandaict.plot import create_plot
from pandaict.topology.routing import *
from pandaict.utils.enums import *
from pandaict.reliability.mtbr_mttf import *

# // *********************************
# //        Network Topology
# //
# //                TCP
# //  App_A <----------------> App_B
# //   |                          |
# //   |            n1            |
# //   |           / | \          |
# //   |        2 /  6  \ 3       |
# //   |    0    /   |   \    1   |
# // dev_A --- n0 -7-+--- n2 --- dev_B
# //             \   |   /
# //            5 \  |  / 4
# //               \ | /
# //                n3
# //
# // *********************************

# set simulation parameters
link_type_01 = 'UMTS'
link_type_12 = 'Fiber'
link_type_23 = 'UMTS'
link_type_03 = 'Fiber'
link_type_13 = 'Fiber'
link_type_02 = 'UMTS'

protocol = 'TCP'        # 20 Byte Packet Size
frequency = 1           # ms

# initialize reliability metrics
MTBF_0 = 1
MTBF_1 = 1
MTBF_2 = 1
MTBF_3 = 1

MTTR_0 = 1
MTTR_1 = 1
MTTR_2 = 1
MTTR_3 = 1

# declare network
net = pi.create_empty_network("4n-Net")

# declare nodes
n0 = pi.create_ict_node(net, name="n0", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_13, link_type_23, link_type_03], mtbf_h=MTBF_0, mttr_h=MTTR_0)
n1 = pi.create_ict_node(net, name="n1", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_13, link_type_23, link_type_03], mtbf_h=MTBF_1, mttr_h=MTTR_1)
n2 = pi.create_ict_node(net, name="n2", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_13, link_type_23, link_type_03], mtbf_h=MTBF_2, mttr_h=MTTR_2)
n3 = pi.create_ict_node(net, name="n3", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_13, link_type_23, link_type_03], mtbf_h=MTBF_3, mttr_h=MTTR_3)

# declare devices
d0 = pi.create_ict_device(net, name='d0', device_type=DeviceType.SERVER)
d2 = pi.create_ict_device(net, name='d1', device_type=DeviceType.SERVER)

# connect devices to their respective nodes
link0 = pi.create_ict_link(net, name='link0', link_type='LAN1000', from_elt=d0, to_elt=[n0])
link2 = pi.create_ict_link(net, name='link1', link_type='LAN1000', from_elt=n2, to_elt=[d2])

# connect nodes
link01 = pi.create_ict_link(net, name='link01', link_type=link_type_01, from_elt=n0, to_elt=[n1])
link12 = pi.create_ict_link(net, name='link12', link_type=link_type_12, from_elt=n1, to_elt=[n2])
link23 = pi.create_ict_link(net, name='link23', link_type=link_type_23, from_elt=n2, to_elt=[n3])
link03 = pi.create_ict_link(net, name='link34', link_type=link_type_03, from_elt=n3, to_elt=[n0])
link13 = pi.create_ict_link(net, name='link13', link_type=link_type_13, from_elt=n1, to_elt=[n3])
link02 = pi.create_ict_link(net, name='link02', link_type=link_type_02, from_elt=n0, to_elt=[n2])

# install apps
app0 = pi.create_ict_app(net, name='appA', app_type=AppType.CLIENT, device=d0)
app2 = pi.create_ict_app(net, name='appB', app_type=AppType.WEBSERVER, device=d2)

# setup connection
Connection_AB = pi.create_ict_connection(
    net,
    name='Connection_AB',
    from_app=app0,
    to_app=app2,
    protocol=protocol,
    info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
    peers=(app0, app2),
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
Links = calc_sorted_links_by_connection(net, Connection_AB, routing_type=RoutingType.LOWEST_TOTAL_LATENCY)
Links = Links[0][0]['links']
print(Links)

Links = [('link', 0), ('link', 5), ('link', 6), ('link', 3), ('link', 1)]

print('\n-------- MTBF along Route --------')
print(calc_MTBF_route(net, Links))

print('\n-------- LINK BANDWIDTH --------')
print(calc_link_bandwidth_Mbps(net, lup))


