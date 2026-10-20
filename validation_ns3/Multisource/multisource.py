import pandaict as pi
import pandaict.diagnosis
from pandaict.plot import create_plot
from pandaict.topology.routing import *
from pandaict.utils.enums import *

# // *********************************************
# //                Network Topology
# //
# //                TCP           TCP
# //        App_A ------> App_C <------ App_B
# //        |               |               |
# //        |               |               |
# //        |              dev_C            |
# //        |               ||              |
# //        |               2|              |
# //        |               ||              |
# //        |               n3              |
# //        |               ||              |
# //        |               5|              |
# //        |               ||              |
# //       dev_A =0= n0 =3= n2 =4= n1 =1= dev_B
# //
# //
# // *********************************************

# set simulation parameters
link_type_02 = 'ADSL8'
link_type_12 = 'ADSL8'
link_type_23 = 'ADSL8' # ADSL8 to easily exceed bandwidth / Overload link

protocol = 'TCP'        # 20 Byte Packet Size
frequency = 0.01        # ms

# declare network
net = pi.create_empty_network("4Net_1")

# declare nodes
n0 = pi.create_ict_node(net, name="n0", node_type=NodeType.ROUTER, link_types=[link_type_02, link_type_12, link_type_23])
n1 = pi.create_ict_node(net, name="n1", node_type=NodeType.ROUTER, link_types=[link_type_02, link_type_12, link_type_23])
n2 = pi.create_ict_node(net, name="n2", node_type=NodeType.ROUTER, link_types=[link_type_02, link_type_12, link_type_23])
n3 = pi.create_ict_node(net, name="n3", node_type=NodeType.ROUTER, link_types=[link_type_02, link_type_12, link_type_23])

# declare devices
d0 = pi.create_ict_device(net, name='d0', device_type=DeviceType.SERVER)
d1 = pi.create_ict_device(net, name='d1', device_type=DeviceType.SERVER)
d3 = pi.create_ict_device(net, name='d3', device_type=DeviceType.SERVER)

# connect devices to their respective nodes
link0 = pi.create_ict_link(net, name='link0', link_type='LAN1000', from_elt=d0, to_elt=[n0])
link1 = pi.create_ict_link(net, name='link1', link_type='LAN1000', from_elt=d1, to_elt=[n1])
link3 = pi.create_ict_link(net, name='link3', link_type='LAN1000', from_elt=d3, to_elt=[n3])

# connect nodes
link02 = pi.create_ict_link(net, name='link02', link_type=link_type_02, from_elt=n0, to_elt=[n2])
link12 = pi.create_ict_link(net, name='link12', link_type=link_type_12, from_elt=n1, to_elt=[n2])
link23 = pi.create_ict_link(net, name='link23', link_type=link_type_23, from_elt=n2, to_elt=[n3])

# install apps on nodes
app0 = pi.create_ict_app(net, name='appA', app_type=AppType.CLIENT, device=d0)
app1 = pi.create_ict_app(net, name='appB', app_type=AppType.CLIENT, device=d1)
app3 = pi.create_ict_app(net, name='appC', app_type=AppType.WEBSERVER, device=d3)

# create connection between apps
Connection_AC = pi.create_ict_connection(
    net,
    name='Connection_AC',
    from_app=app0,
    to_app=app3,
    protocol=protocol,
    info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
    peers=(app0, app3),
    producer=[0,1],
    prod_freq_ms=[frequency, -1]
)

# create connection between apps
Connection_BC = pi.create_ict_connection(
    net,
    name='Connection_BC',
    from_app=app1,
    to_app=app3,
    protocol=protocol,
    info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
    peers=(app1, app3),
    producer=[0,1],
    prod_freq_ms=[frequency, -1]
)

pandaict.diagnosis.inspect(net)

print('\n-------- ROUTES FOR CONNECTION --------')
print('Connection_AC: ', calc_routes_for_connection(net, Connection_AC))
print('Connection_BC: ', calc_routes_for_connection(net, Connection_BC))

lupAC = calc_lup_table(net, Connection_AC, routing_type=RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True)
lupBC = calc_lup_table(net, Connection_BC, routing_type=RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True)

print('\n-------- CONNECTION BANDWIDTH --------')
print('Connection_AC: ', calc_conn_bandwidth_Mbps(net, Connection_AC))
print('Connection_BC: ', calc_conn_bandwidth_Mbps(net, Connection_BC))

print('\n-------- LINKS FOR CONNECTION --------')
print('Connection_AC: ', calc_sorted_links_by_connection(net, Connection_AC, routing_type=RoutingType.LOWEST_TOTAL_LATENCY))
print('Connection_BC: ', calc_sorted_links_by_connection(net, Connection_BC, routing_type=RoutingType.LOWEST_TOTAL_LATENCY))

print('\n-------- LINK BANDWIDTH --------')
print('Connection_AC: ', calc_link_bandwidth_Mbps(net, lupAC))
print('Connection_BC: ', calc_link_bandwidth_Mbps(net, lupBC))


