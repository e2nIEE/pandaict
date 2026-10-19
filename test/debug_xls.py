import pandaict as pi
from pandaict.utils.enums import NodeType, DeviceType, AppType, InfoItem
from pandaict.toolbox.exceltools import to_excel, from_excel
from pandaict.reliability.mtbf_mttr import calc_mtbf_route, calc_mtbf_mttr_route
import os
from utils.enums import add_custom_enum

def create_net():
    net = pi.create_empty_network(name='Demo_net')
    
    n_1  = pi.create_ict_node(net,  name='node 1',  node_type=NodeType.ROUTER, link_types=['Fiber','LAN1000'], mtbf_h=1000, mttr_h=1)
    n_2   = pi.create_ict_node(net, name='node 2',  node_type=NodeType.SWITCH, link_types=['LAN1000'], mtbf_h=1000, mttr_h=1)
    n_3   = pi.create_ict_node(net, name='node 3',  node_type=NodeType.SWITCH, link_types=['LAN1000'], mtbf_h=1000, mttr_h=1)
    
    server  = pi.create_ict_device(net, name='CTRL-server', device_type=DeviceType.SERVER, mtbf_h=5000, mttr_h=4)
    rtu     = pi.create_ict_device(net, name='rtu-A',       device_type=DeviceType.RTU, mtbf_h=2000, mttr_h=2)
    
    pi.create_ict_link(net, name='L-n1-n2',   from_elt=n_1,  to_elt=[n_2],   link_type='LAN1000')
    pi.create_ict_link(net, name='L-n2-n3',   from_elt=n_2,  to_elt=[n_3],   link_type='LAN1000')
    pi.create_ict_link(net, name='L-n1-n3',   from_elt=n_1,  to_elt=[n_3],   link_type='LAN1000')
    pi.create_ict_link(net, name='L-serv-n1',   from_elt=server,  to_elt=[n_1],   link_type='LAN1000')
    pi.create_ict_link(net, name='L-n3-rtu',   from_elt=n_3,  to_elt=[rtu],   link_type='LAN1000')
    
    app_ser = pi.create_ict_app(net, name='App-server',  app_type=AppType.CLIENT,    device=server)
    app_rtu = pi.create_ict_app(net, name='App-rtu', app_type=AppType.WEBSERVER, device=rtu)

    return net, app_ser, app_rtu


def check_from_to_xls(net):
    passed = pi.inspect(net, verbose=True)
    print('\nAll checks passed:', passed)

    # Export
    to_excel(net, 'demo_network1.xlsx')
    print('Exported to demo_network1.xlsx')

    # Import
    loaded = from_excel('demo_network1.xlsx')
    print('Import done.')
    
    return loaded 

def create_conn_retest_xls(net, app_ser, app_rtu):
    pi.create_ict_connection(net, name='CTRL-to-RTU-A',
    from_app=app_ser, to_app=app_rtu, protocol='TCP',
    info_items=[InfoItem.REQUEST, InfoItem.VALUE],
    peers=(app_ser, app_rtu), producer=[0, 1])
    
    passed = pi.inspect(net, verbose=True)
    print('\nAll checks passed:', passed)
    
    # Export
    to_excel(net, 'demo_network2.xlsx')
    print('Exported to demo_network2.xlsx')
    
    # Import
    from_excel('demo_network2.xlsx')
    print('Import done.')
    
    
net, app_ser, app_rtu = create_net()

pi.create_ict_connection(net, name="Conn", from_app=('app',0), to_app=('app',1))
r = [('link', 3), ('link', 2), ('link', 4)]
rrev = [('link', 4), ('link', 2), ('link', 3)]

ied = True
print(str(calc_mtbf_route(net, r, include_end_devices=ied)))
print(str(calc_mtbf_mttr_route(net, r, include_end_devices=ied)))
print(str(calc_mtbf_route(net, rrev, include_end_devices=ied)))
print(str(calc_mtbf_mttr_route(net, rrev, include_end_devices=ied)))


print("A")