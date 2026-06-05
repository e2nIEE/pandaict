import pandaict as pi
from pandaict.utils.enums import NodeType, DeviceType, AppType, InfoItem
from pandaict.toolbox.exceltools import to_excel, from_excel
import os

def create_net():
    net = pi.create_empty_network(name='Demo_net')
    
    n_1  = pi.create_ict_node(net,  name='node 1',  node_type=NodeType.ROUTER, link_types=['Fiber','LAN1000'])
    n_2   = pi.create_ict_node(net, name='node 2',  node_type=NodeType.SWITCH, link_types=['LAN1000'])
    n_3   = pi.create_ict_node(net, name='node 3',  node_type=NodeType.SWITCH, link_types=['LAN1000'])
    
    Server  = pi.create_ict_device(net, name='CTRL-Server', device_type=DeviceType.SERVER)
    RTU     = pi.create_ict_device(net, name='RTU-A',       device_type=DeviceType.RTU)
    
    pi.create_ict_link(net, name='L-n1-n2',   from_elt=n_1,  to_elt=[n_2],   link_type='LAN1000')
    pi.create_ict_link(net, name='L-n2-n3',   from_elt=n_2,  to_elt=[n_3],   link_type='LAN1000')
    pi.create_ict_link(net, name='L-n1-n3',   from_elt=n_1,  to_elt=[n_3],   link_type='LAN1000')
    
    app_ser = pi.create_ict_app(net, name='App-Server',  app_type=AppType.CLIENT,    device=Server)
    app_rtu = pi.create_ict_app(net, name='App-RTU', app_type=AppType.WEBSERVER, device=RTU)

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
    loaded = from_excel('demo_network2.xlsx')
    print('Import done.')
    
    
net, app_ser, app_rtu = create_net()
loaded = check_from_to_xls(net)
loaded = from_excel('demo_network1.xlsx')
create_conn_retest_xls(loaded, app_ser, app_rtu)