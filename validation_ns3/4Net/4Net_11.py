import pandaict as pi
import pandaict.diagnosis
from pandaict.topology.routing import *
from pandaict.utils.enums import *
from pandaict.reliability.mtbr_mttf import *
from pandaict.reliability.ber import *

# // *********************************
# //        Network Topology
# //
# //               TCP
# //  App_A <----------------> App_B
# //   |                         |
# //   |            n1           |
# //   |           /  \          |
# //   |        2 /    \ 3       |
# //   |     0   /      \   1    |
# //  dev_A --- n0      n2 --- dev_B
# //             \      /
# //            5 \    / 4
# //               \  /
# //                n3
# //
# // *********************************

# set simulation parameters
link_type_01 = 'Fiber'
link_type_12 = 'Fiber'
link_type_23 = 'Fiber'
link_type_03 = 'Fiber'

protocol = 'TCP'        # 20 Byte Packet Size
frequency = 1           # ms

BER_0 = 0
BER_1 = 0.5
BER_2 = 0.5
BER_3 = 0.5

MTBF0 = 0
MTBF1 = 0.1
MTBF2 = 0
MTBF3 = 1

MTTR0 = 0
MTTR1 = 0
MTTR2 = 0
MTTR3 = 0


# declare network
net = pi.create_empty_network("4Net_1")

# declare nodes
n0 = pi.create_ict_node(net, name="n0", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_03, link_type_23], ber=BER_0, mtbf_h=MTBF0, mttr_h=MTTR0)
n1 = pi.create_ict_node(net, name="n1", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_03, link_type_23], ber=BER_1, mtbf_h=MTBF1, mttr_h=MTTR1)
n2 = pi.create_ict_node(net, name="n2", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_03, link_type_23], ber=BER_2, mtbf_h=MTBF2, mttr_h=MTTR2)
n3 = pi.create_ict_node(net, name="n3", node_type=NodeType.ROUTER, link_types=[link_type_01, link_type_12, link_type_03, link_type_23], ber=BER_3, mtbf_h=MTBF3, mttr_h=MTTR3)

# declare devices
d0 = pi.create_ict_device(net, name='d0', device_type=DeviceType.SERVER)
d2 = pi.create_ict_device(net, name='d2', device_type=DeviceType.SERVER)

# connect devices to their respective nodes
link0 = pi.create_ict_link(net, name='link0', link_type='LAN1000', from_elt=d0, to_elt=[n0])
link2 = pi.create_ict_link(net, name='link2', link_type='LAN1000', from_elt=n2, to_elt=[d2])

# connect nodes
link01 = pi.create_ict_link(net, name='link02', link_type=link_type_01, from_elt=n0, to_elt=[n1])
link12 = pi.create_ict_link(net, name='link12', link_type=link_type_12, from_elt=n1, to_elt=[n2])
link23 = pi.create_ict_link(net, name='link23', link_type=link_type_23, from_elt=n2, to_elt=[n3])
link03 = pi.create_ict_link(net, name='link34', link_type=link_type_03, from_elt=n0, to_elt=[n3])

# install apps on nodes
app0 = pi.create_ict_app(net, name='appA', app_type=AppType.CLIENT, device=d0)
app3 = pi.create_ict_app(net, name='appB', app_type=AppType.WEBSERVER, device=d2)

# create connection between apps
Connection_AB = pi.create_ict_connection(
    net,
    name='Connection_AB',
    from_app=app0,
    to_app=app3,
    protocol=protocol,
    info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
    peers=(app0, app3),
    producer=[0,1],
    prod_freq_ms=[frequency, -1]
)

pandaict.diagnosis.inspect(net)
lup = calc_lup_table(net, Connection_AB, routing_type=RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True)

print('\n-------- ROUTES FOR CONNECTION --------')
print(calc_routes_for_connection(net, Connection_AB))

print('\n-------- CONNECTION BANDWIDTH --------')
print(calc_conn_bandwidth_Mbps(net, Connection_AB))

print('\n-------- LINKS FOR CONNECTION --------')
links = calc_sorted_links_by_connection(net, Connection_AB, routing_type=RoutingType.LOWEST_TOTAL_LATENCY)
print(links)

print('\n-------- LINK BANDWIDTH --------')
print(calc_link_bandwidth_Mbps(net, lup))

print('\n-------- BER FOR LUP --------')
BER = calc_ber_by_lup(net, lup, downstream=False)
BER = round(BER, 4)
print(BER)

print('\n-------- BER FROM THEORY --------')
BER = 0

print('\n-------- LUP --------')
print(lup._lupdf)

print('\n----------- MTBF OF SYSTEM -----------')
MTBF = calc_mtbf_mttr_by_lup(net, lup)
print(MTBF)

