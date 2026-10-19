import pandaict as pi
import pandaict.diagnosis
from pandaict.utils.utils import get_bandwidth_mbps
from pandaict.plot import create_plot
from pandaict.topology.routing import *
from pandaict.utils.enums import *

# //   Network Topology
# //
# //          UDP
# // App_A <-------> App_B
# //   |               |
# // dev_A ========= dev_B
# //        LAN1000
# //

# set simulation parameters
link_type = 'LAN1000'
protocol = 'TCP'        # 8 Byte Packet Size
frequency = 1          # ms

#
net = pi.create_empty_network('simple-net')

# create dummy node to connect devices, since they cant be connected directly
dummy_node = pi.create_ict_node(net, 'dummy-node', node_type=NodeType.ROUTER, link_types=[link_type])

# create ICT devices
device_A = pi.create_ict_device(net, 'Device_A', device_type=DeviceType.SERVER)
device_B = pi.create_ict_device(net, 'Device_B', device_type=DeviceType.SERVER)

#
app_A = pi.create_ict_app(net, name='app_A', device=device_A, app_type=AppType.CLIENT)
app_B = pi.create_ict_app(net, name='app_B', device=device_B, app_type=AppType.WEBSERVER)

# connect ict devices (using dummy node, since two devices cant be connected directly)
Link_A = pi.create_ict_link(net, name='Link_A', from_elt=device_A, to_elt=[dummy_node], link_type=link_type)
Link_B = pi.create_ict_link(net, name='Link_B', from_elt=dummy_node, to_elt=[device_B], link_type=link_type)

# Set up connection between apps
# Let the client produce requests and the Webserver responses.
# Let the frequency of requests be a parameter and the responses event-based.
Connection_AB = pi.create_ict_connection(
    net,
    name='Connection_AB',
    from_app=app_A,
    to_app=app_B,
    protocol=protocol,
    info_items=[InfoItem.REQUEST, InfoItem.RESPONSE],
    peers=(app_A, app_B),
    producer=[0,1],
    prod_freq_ms=[frequency, -1]
)

pandaict.diagnosis.inspect(net)

BW = calc_conn_bandwidth_mbps(net, Connection_AB)

print('Used Bandwidth (upstream, downstream) Mbps = ', BW)

delta_t = 10    # s
total_bytes = BW[0] * delta_t * 10**6 /8

print('Total bytes = ', total_bytes, ' Bytes')

theory = 20 * 100 # byte pro Sekunde
theory = theory * 10**(-6) # MegaByte pro Sekunde
theory = theory * 8 # Megabit pro Sekunde

print('theoretical calculation: BW = ', theory, 'Mbps')
