import pandaict as pi
import pandaict.diagnosis
from pandaict.plot import create_plot
from pandaict.topology.routing import *
from pandaict.utils.enums import *
from pandaict.utils.utils import *
from pandaict.reliability.mtbr_mttf import *
from pandaict.reliability.ber import *
import numpy as np

# // ******************************************
# //           Network Topology
# //
# //                + ---- PQ2
# //                |
# //                |+ --- PQ1
# //                ||
# //  CC --- n1 --- n2 --- conv1 --- PC1
# //                ||
# //                |+ --- conv2 --- PC2
# //                |
# //                +  --- conv3 --- PC3
# //
# // ******************************************

# ----------------------
# SIMULATION PARAMETERS
# ----------------------
# link types
linktype1 = 'Fiber'
linktype2 = 'Fiber'
linktype3 = 'Fiber'
linktype4 = 'Fiber'
linktype5 = 'Fiber'
linktype6 = 'Fiber'
linktype7 = 'Fiber'
linktype8 = 'Fiber'
linktype9 = 'Fiber'
linktype10 = 'Fiber'

length = 0.2
length1 = length
length2 = length
length3 = length
length4 = length
length5 = length
length6 = length
length7 = length
length8 = length
length9 = length
length10= length

# connection protocols
protocol1 = 'TCP'        # 20 Byte Packet Size
protocol2 = 'TCP'        # 20 Byte Packet Size
protocol3 = 'TCP'        # 20 Byte Packet Size
protocol4 = 'TCP'        # 20 Byte Packet Size
protocol5 = 'TCP'        # 20 Byte Packet Size
protocol6 = 'TCP'        # 20 Byte Packet Size
protocol7 = 'TCP'        # 20 Byte Packet Size
protocol8 = 'TCP'        # 20 Byte Packet Size

# connection period
frequency = 1           # ms

# BER on nodes
BER = 0

BER0 = BER
BER1 = BER
BER2 = BER
BER3 = BER
BER4 = BER
BER5 = BER
BER6 = BER
BER7 = BER
BER8 = BER
BER9 = BER
BER10 = BER


# declare MTBF & MTTR on nodes/devices
MTBF = 0

MTBF0 = MTBF
MTBF1 = MTBF
MTBF2 = MTBF
MTBF3 = MTBF
MTBF4 = MTBF
MTBF5 = MTBF
MTBF6 = MTBF
MTBF7 = MTBF
MTBF8 = MTBF
MTBF9 = MTBF
MTBF10 = MTBF

MTTR0 = 0
MTTR1 = 0
MTTR2 = 0
MTTR3 = 0
MTTR4 = 0
MTTR5 = 0
MTTR6 = 0
MTTR7 = 0
MTTR8 = 0
MTTR9 = 0
MTTR10 = 0

ict_net = pi.create_empty_network("pandaict<->pandapower-connector", True)

# create nodes
node1 = pi.create_ict_node(ict_net, name="Node1", node_type=NodeType.ROUTER,
                           link_types=["Fiber", "LAN1000"], mtbf_h=MTBF1, mttr_h=MTTR1, ber=BER1)
node2 = pi.create_ict_node(ict_net, name="Node2", node_type=NodeType.ROUTER,
                           link_types=["Fiber", "LAN1000", "ADSL8", "LTE50"], mtbf_h=MTBF2, mttr_h=MTTR2, ber=BER2)

# create devices
dconv1 = pi.create_ict_device(ict_net, name='Conv1', device_type=pi.DeviceType.CONVERTER, mtbf_h=MTBF3, mttr_h=MTTR3)
dconv2 = pi.create_ict_device(ict_net, name='Conv2', device_type=pi.DeviceType.CONVERTER, mtbf_h=MTBF4, mttr_h=MTTR4)
dconv3 = pi.create_ict_device(ict_net, name='Conv3', device_type=pi.DeviceType.CONVERTER, mtbf_h=MTBF5, mttr_h=MTTR5)
dcc = pi.create_ict_device(ict_net, name='CC', device_type=pi.DeviceType.SERVER, mtbf_h=MTBF0, mttr_h=MTTR0)
dpq1 = pi.create_ict_device(ict_net, name='PQ1', device_type=pi.DeviceType.RTU, mtbf_h=MTBF6, mttr_h=MTTR6)
dpq2 = pi.create_ict_device(ict_net, name='PQ2', device_type=pi.DeviceType.RTU, mtbf_h=MTBF7, mttr_h=MTTR7)
dsc = pi.create_ict_device(ict_net, name='SC', device_type=pi.DeviceType.RTU, mtbf_h=MTBF10, mttr_h=MTTR10)
dpc1 = pi.create_ict_device(ict_net, name='PC1', device_type=pi.DeviceType.RTU, mtbf_h=MTBF8, mttr_h=MTTR8)
dpc2 = pi.create_ict_device(ict_net, name='PC2', device_type=pi.DeviceType.RTU, mtbf_h=MTBF9, mttr_h=MTTR9)

# create apps
aconv1 = pi.create_ict_app(ict_net, name='Conv_app1', app_type=AppType.CONVERTER, device=dconv1)
aconv2 = pi.create_ict_app(ict_net, name='Conv_app2', app_type=AppType.CONVERTER, device=dconv2)
aconv3 = pi.create_ict_app(ict_net, name='Conv_app3', app_type=AppType.CONVERTER, device=dconv3)
acc = pi.create_ict_app(ict_net, name='CC_app', app_type=AppType.WEBSERVER, device=dcc)
apq1 = pi.create_ict_app(ict_net, name='PQ1_app', app_type=AppType.CLIENT, device=dpq1)
apq2 = pi.create_ict_app(ict_net, name='PQ2_app', app_type=AppType.CLIENT, device=dpq2)
asc = pi.create_ict_app(ict_net, name='SC_APP', app_type=AppType.CLIENT, device=dsc)
apc1 = pi.create_ict_app(ict_net, name='PC1_APP', app_type=AppType.CLIENT, device=dpc1)
apc2 = pi.create_ict_app(ict_net, name='PC2_APP', app_type=AppType.CLIENT, device=dpc2)

# create links
link1 = pi.create_ict_link(ict_net, name="CC_Node1", link_type=linktype1, from_elt=dcc, to_elt=[node1], length_km=length1)
link2 = pi.create_ict_link(ict_net, name="Node1_Node2", link_type=linktype2, from_elt=node1, to_elt=[node2], length_km=length2)
link3 = pi.create_ict_link(ict_net, name="Node2_Conv1", link_type=linktype3, from_elt=node2, to_elt=[dconv1], length_km=length3)
link4 = pi.create_ict_link(ict_net, name="Node2_Conv2", link_type=linktype4, from_elt=node2, to_elt=[dconv2], length_km=length4)
link5 = pi.create_ict_link(ict_net, name="Node2_Conv3", link_type=linktype5, from_elt=node2, to_elt=[dconv3], length_km=length5)
link6 = pi.create_ict_link(ict_net, name="Node2_PQ1", link_type=linktype6, from_elt=node2, to_elt=[dpq1], length_km=length6)
link7 = pi.create_ict_link(ict_net, name="Node2_PQ2", link_type=linktype7, from_elt=node2, to_elt=[dpq2], length_km=length7)
link8 = pi.create_ict_link(ict_net, name="Conv1_PC1", link_type=linktype8, from_elt=dconv1, to_elt=[dpc1], length_km=length8)
link9 = pi.create_ict_link(ict_net, name="Conv2_PC2", link_type=linktype9, from_elt=dconv2, to_elt=[dpc2], length_km=length9)
link10 = pi.create_ict_link(ict_net, name="Conv3_SC", link_type=linktype10, from_elt=dconv3, to_elt=[dsc], length_km=length10)

# create connections between apps TODO: CHECK CONN5
conn1 = pi.create_ict_connection(ict_net, name="CC_Conv1", from_app=acc, to_app=aconv1, protocol=protocol1,
                                 info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
                                 peers=(acc, aconv1),
                                 producer=[1,0],
                                 prod_freq_ms=[frequency, 0])
conn2 = pi.create_ict_connection(ict_net, name="Conv1_PC1", from_app=aconv1, to_app=apc1, protocol=protocol2,
                                 info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
                                 peers=(aconv1, apc1),
                                 producer=[1,0],
                                 prod_freq_ms=[frequency, 0])
conn3 = pi.create_ict_connection(ict_net, name="CC_PQ1", from_app=acc, to_app=apq1, protocol=protocol3,
                                 info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
                                 peers=(acc, apq1),
                                 producer=[1,0],
                                 prod_freq_ms=[frequency, 0])
conn4 = pi.create_ict_connection(ict_net, name=" CC_Conv2", from_app=acc, to_app=aconv2, protocol=protocol4,
                                 info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
                                 peers=(acc, aconv2),
                                 producer=[1,0],
                                 prod_freq_ms=[frequency, 0])
conn5 = pi.create_ict_connection(ict_net, name="Conv2_PC2", from_app=aconv2, to_app=apc2, protocol=protocol5,
                                 info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
                                 peers=(aconv2, apc2),
                                 producer=[1,0],
                                 prod_freq_ms=[frequency, 0])
conn6 = pi.create_ict_connection(ict_net, name="CC_PQ2", from_app=acc, to_app=apq2, protocol=protocol6,
                                 info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
                                 peers=(acc, apq2),
                                 producer=[1,0],
                                 prod_freq_ms=[frequency, 0])
conn7 = pi.create_ict_connection(ict_net, name="CC_Conv3", from_app=acc, to_app=aconv3, protocol=protocol7,
                                 info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
                                 peers=(aconv1, apc1),
                                 producer=[1,0],
                                 prod_freq_ms=[frequency, 0])
conn8 = pi.create_ict_connection(ict_net, name="Conv3_SC", from_app=aconv3, to_app=asc, protocol=protocol8,
                                 info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
                                 peers=(aconv3, asc),
                                 producer=[1,0],
                                 prod_freq_ms=[frequency, 0])


if pandaict.diagnosis.inspect(ict_net):

    net = ict_net

    connections = [conn1, conn2, conn3, conn4, conn5, conn6, conn7, conn8]
    links = [link1, link2, link3, link4, link5, link6, link7, link8, link9, link10]

    print('\n-------- USED BANDWIDTH BY CONNECTIONS --------')
    for i, conn in enumerate(connections):
        print('Connection', i+1, ': ', calc_conn_bandwidth_Mbps(ict_net, conn), 'Mbps (Down, Up)')


    print('\n-------- LINK USAGE --------')
    Total_BW = {0: [0, 0], 1: [0, 0], 2: [0, 0], 3: [0, 0], 4: [0, 0], 5: [0, 0], 6: [0, 0], 7: [0, 0], 8: [0, 0],
                9: [0, 0]}

    # calc link usage on all links
    for connection in connections:
        lup_ = calc_lup_table(net, connection, routing_type=RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True)
        BW = calc_link_bandwidth_Mbps(net, lup_)
        for key in BW:
            Total_BW[key] = np.add(Total_BW[key], BW[key]).tolist()

    for key in Total_BW:
        print('link', key+1, ':', Total_BW[key], 'Mbps [Down, Up]')

    print('\n-------- ROUTES FOR CONNECTION --------')
    for i, conn in enumerate(connections):
        print('Connection', i+1, ': ', calc_routes_for_connection(ict_net, conn))

    print('\n-------- LINKS FOR CONNECTION --------')
    for i, conn in enumerate(connections):
        print('Connection', i+1,': ', calc_sorted_links_by_connection(net, conn, routing_type=RoutingType.LOWEST_TOTAL_LATENCY))

    print('\n-------- BER ON LINKS --------')
    # link2 is between two nodes which apparently sets BER to 0
    for i, link in enumerate(links):
        print(calc_ber_route(ict_net, [links[i]]))

    print('\n-------- BER PER CONNECTION --------')
    for i, conn in enumerate(connections):
        lup_ = calc_lup_table(net, conn, routing_type=RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True)
        BER = calc_ber_by_lup(net, lup_, downstream=False)
        BER = round(BER, 4)
        print('conn', i+1, ': ', BER)

    print('\n----------- MTBF/MTTR OF SYSTEM -----------')
    for i, conn in enumerate(connections):
        lup_ = calc_lup_table(net, conn, routing_type=RoutingType.LOWEST_TOTAL_LATENCY, include_hops=True)
        MTBF, MTTR = calc_mtbf_mttr_by_lup(net, lup_, include_end_app=False)
        print('conn', i+1, ':')
        print('     MTBF =', round(MTBF, 4))
        print('     MTTR =', round(MTTR, 4))
