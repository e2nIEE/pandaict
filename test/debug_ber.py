import pandaict as pi
from pandaict.topology.routing import *
from pandaict.utils.enums import *
from pandaict.reliability.ber import *


BER_nodes = 1
link_type = 'Fiber'
protocol = 'TCP'

# declare network
net = pi.create_empty_network("ict-net")

n1 = pi.create_ict_node(net,
                        name="n1",
                        node_type=NodeType.ROUTER,
                        link_types=[link_type],
                        ber=BER_nodes)

n2 = pi.create_ict_node(net,
                        name="n2",
                        node_type=NodeType.ROUTER,
                        link_types=[link_type],
                        ber=BER_nodes)

# declare devices
dcc = pi.create_ict_device(net, name='dcc', device_type=DeviceType.SERVER)
dconv1 = pi.create_ict_device(net, name='dconv1', device_type=DeviceType.CONVERTER)

# connect devices to their respective nodes
link1 = pi.create_ict_link(net, name='link1', link_type=link_type, from_elt=n1, to_elt=[n2])
link2 = pi.create_ict_link(net, name='link2', link_type=link_type, from_elt=dcc, to_elt=[n1])
link3 = pi.create_ict_link(net, name='link3', link_type=link_type, from_elt=n2, to_elt=[dconv1])

# install apps on devices
acc = pi.create_ict_app(net, name='acc', app_type=AppType.WEBSERVER, device=dcc)
aconv1 = pi.create_ict_app(net, name='aconv1', app_type=AppType.CONVERTER, device=dconv1)

# create connection between apps
conn1 = pi.create_ict_connection(
    net,
    name='conn1',
    from_app=acc,
    to_app=aconv1,
    protocol=protocol
)

#BER = calc_ber_route(net, [('link', 1), ('link', 0), ('link', 2)])
BER = calc_ber_route(net, [link2, link1, link3])
print(BER)
