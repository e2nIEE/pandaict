'''
Created on 13.09.2025
@author: fnuetz
'''

import networkx as nx
import random
import statistics
from   pandaict.utils.enums import NodeType, DeviceType, InfoItem, AppType, RoutingType, SortType, add_custom_enum
from   pandaict.create import create_ict_node, create_ict_link, create_ict_device, create_ict_app, create_ict_devapp, create_ict_connection
from   pandaict.create_empty_net import create_empty_network
from   pandaict.topology.routing import is_connection_possible, __modify_multidigraph_by_iptables
from   pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt
from   pandaict.reliability.monte_carlo import estimate_mttf_mttr
from   pandaict import inspect
from aenum import extend_enum

def get_testnet_v1():
    
    net   = create_empty_network()
    add_custom_enum(net, NodeType, "VIRTUAL")
    SWg   = create_ict_node(net, name="SWg", node_type=NodeType.SWITCH, link_types=["LAN1000"])   
    SWb   = create_ict_node(net, name="SWb", node_type=NodeType.SWITCH, link_types=["LAN1000"])
    _f1   = create_ict_node(net, name="_f1", node_type=NodeType.VIRTUAL, link_types=["LAN1000"])   
    _f2   = create_ict_node(net, name="_f2", node_type=NodeType.VIRTUAL, link_types=["LAN1000"])
    
    add_custom_enum(net, DeviceType, "PROTECTION")
    add_custom_enum(net, DeviceType, "VIRTUAL")
    add_custom_enum(net, AppType, "PROTECTION")
    add_custom_enum(net, AppType, "POWERMETER")
    add_custom_enum(net, InfoItem, "ACTIVE_POWER")
    (SGd, SGa) = create_ict_devapp(net, name="SG", device_type=DeviceType.PROTECTION, app_type=AppType.PROTECTION) 
    (_md, _ma) = create_ict_devapp(net, name="_m", device_type=DeviceType.VIRTUAL, app_type=AppType.POWERMETER) 
    FE1 = create_ict_device(net, name="FE1", device_type=DeviceType.RTU)
    FE2 = create_ict_device(net, name="FE2", device_type=DeviceType.RTU)
    
    create_ict_link(net, name="L1",  link_type="LAN1000", from_elt=SGd, to_elt=[SWg], length_km=0.01)
    create_ict_link(net, name="L2",  link_type="LAN1000", from_elt=SGd, to_elt=[SWb], length_km=0.01)
    create_ict_link(net, name="L3",  link_type="LAN1000", from_elt=SWg, to_elt=[FE1], length_km=0.01)
    create_ict_link(net, name="L4",  link_type="LAN1000", from_elt=SWg, to_elt=[FE2], length_km=0.01)
    create_ict_link(net, name="L5",  link_type="LAN1000", from_elt=SWb, to_elt=[FE1], length_km=0.01)
    create_ict_link(net, name="L6",  link_type="LAN1000", from_elt=SWb, to_elt=[FE2], length_km=0.01)
    create_ict_link(net, name="vL1", link_type="LAN1000", from_elt=FE1, to_elt=[_f1], length_km=0.01)
    create_ict_link(net, name="vL2", link_type="LAN1000", from_elt=FE2, to_elt=[_f2], length_km=0.01)
    create_ict_link(net, name="vL3", link_type="LAN1000", from_elt=_f1, to_elt=[_md], length_km=0.01)
    create_ict_link(net, name="vL4", link_type="LAN1000", from_elt=_f2, to_elt=[_md], length_km=0.01)
    
    create_ict_connection(net, name="Conn1", from_app=_ma, to_app=SGa, protocol="TCP",
                        info_items=[InfoItem.ACTIVE_POWER], 
                        peers=(_ma,SGa), producer=[0], prod_freq_ms=[10000])                   
    return net
    
    
def get_testnet_v2():
    
    net   = create_empty_network()
    add_custom_enum(net, NodeType, "COUPLER")
    SWg   = create_ict_node(net, name="SWg", node_type=NodeType.SWITCH, link_types=["LAN1000"], mtbf_h=2000, mttr_h=2000)   
    SWb   = create_ict_node(net, name="SWb", node_type=NodeType.SWITCH, link_types=["LAN1000"], mtbf_h=2000, mttr_h=2000)
    FE1   = create_ict_node(net, name="FE1", node_type=NodeType.COUPLER, link_types=["LAN1000"], mtbf_h=2000, mttr_h=2000)
    FE2   = create_ict_node(net, name="FE2", node_type=NodeType.COUPLER, link_types=["LAN1000"], mtbf_h=2000, mttr_h=2000)
    
    add_custom_enum(net, DeviceType, "VIRTUAL")
    add_custom_enum(net, DeviceType, "PROTECTION")
    add_custom_enum(net, AppType, "PROTECTION")
    add_custom_enum(net, AppType, "POWERMETER")
    add_custom_enum(net, InfoItem, "ACTIVE_POWER")
    (SGd, SGa) = create_ict_devapp(net, name="SG", device_type=DeviceType.PROTECTION, app_type=AppType.PROTECTION) 
    (_md, _ma) = create_ict_devapp(net, name="_m", device_type=DeviceType.VIRTUAL, app_type=AppType.POWERMETER) 
    
    create_ict_link(net, name="L1",  link_type="LAN1000", from_elt=SGd, to_elt=[SWg], length_km=0.01)
    create_ict_link(net, name="L2",  link_type="LAN1000", from_elt=SGd, to_elt=[SWb], length_km=0.01)
    create_ict_link(net, name="L3",  link_type="LAN1000", from_elt=SWg, to_elt=[FE1], length_km=0.01)
    create_ict_link(net, name="L4",  link_type="LAN1000", from_elt=SWg, to_elt=[FE2], length_km=0.01)
    create_ict_link(net, name="L5",  link_type="LAN1000", from_elt=SWb, to_elt=[FE1], length_km=0.01)
    create_ict_link(net, name="L6",  link_type="LAN1000", from_elt=SWb, to_elt=[FE2], length_km=0.01)
    create_ict_link(net, name="vL3", link_type="LAN1000", from_elt=FE1, to_elt=[_md], length_km=0.01)
    create_ict_link(net, name="vL4", link_type="LAN1000", from_elt=FE2, to_elt=[_md], length_km=0.01)
    
    create_ict_connection(net, name="Conn1", from_app=_ma, to_app=SGa, protocol="TCP",
                        info_items=[InfoItem.ACTIVE_POWER], 
                        peers=(_ma,SGa), producer=[0], prod_freq_ms=[10000])                   
    return net


def _get_montecarlo_nxgraph(ict_net, conn, downstream=True, respect_iptables=False):
    
    mdg = create_multidigraph(ict_net, conn['protocol'], validate=True)    
    from_dev = ('device', ict_net.app.iloc[conn['from']]['device'])
    to_dev = ('device', ict_net.app.iloc[conn['to']]['device'])
    if not downstream:
        from_dev, to_dev = to_dev, from_dev
    if respect_iptables:        
        __modify_multidigraph_by_iptables(ict_net, mdg, to_dev)  
    from_nxnode = __get_nx_node_for_elt(mdg, from_dev)
    to_nxnode = __get_nx_node_for_elt(mdg, to_dev)  
    
    for n in mdg.nodes():
        ndata = mdg.nodes(data=True)[n]
        pinode = ndata['pielt']
        mtbf = ict_net[pinode[0]].loc[pinode[1]]['mtbf_h']/1000 
        mttr = ict_net[pinode[0]].loc[pinode[1]]['mttr_h']/1000
        ndata.update({'mtbf_h': mtbf, 'mttr_h': mttr})
        nx.set_node_attributes(mdg, {n: ndata})
    
    for e in mdg.edges():
        edata = mdg.get_edge_data(e[0], e[1])[0]
        piedge = edata['pielt'] 
        ltype = ict_net.std_types['link'][ict_net[piedge[0]].loc[piedge[1]]['type']]        
        mtbf = ltype['mtbf_h']/1000 
        mttr = ltype['mttr_h']/1000
        edata.update({'mtbf_h': mtbf, 'mttr_h': mttr})
        nx.set_node_attributes(mdg, {e: edata})
    
    return mdg, from_nxnode, to_nxnode
    
    
    
if __name__ == "__main__":
    net = get_testnet_v2()
    conn = net.conn.loc[0]
    G, source, target = _get_montecarlo_nxgraph(net, conn)
    mttf, mttr = estimate_mttf_mttr(G, source, target, N=10)
    print("MTTF:", round(mttf, 3))
    print("MTTR:", round(mttr, 3))
    print("MTBF:", round(mttf+mttr, 3))

    