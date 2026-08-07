import pandaict as pi
import pandaict.topology.routing as piroute

net = pi.create_empty_network()
dserv, aserv = pi.create_ict_devapp(net)
dcli, acli  = pi.create_ict_devapp(net)
node = pi.create_ict_node(net, pi.NodeType.ROUTER)
pi.create_ict_link(net, from_elt=dserv, to_elt=node, link_type='Fiber')
pi.create_ict_link(net, from_elt=node, to_elt=dcli, link_type='LAN1000')
conn = pi.create_ict_connection(net, from_app=aserv, to_app=acli, protocol='TCP')

routes = piroute.calc_routes_for_connection(net, conn)

print(str(routes))