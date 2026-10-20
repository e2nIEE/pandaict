'''
Created on 29.07.2026
@author: fnuetz
'''
import pandaict as pi

DEV_TYPE = None     # DeviceType.SERVER
APP_TYPE = None     # AppType.WEBSERVER
NODE_TYPE = None    # NodeType.ROUTER


def build_test_ict_network(n, m, mttf_h, mttr_h):
    '''
    pandaICT equivalent to build_test_network(...).
        n independent seriell paths of length m
        Only nodes can fail (sources, targets excluded)

        returns (ict_net, connections) analogous to (G, sources, targets)
    '''
    mtbf_h = mttf_h + mttr_h

    net = pi.create_empty_network(name=f'test_network: n={n}, m={m}')

    # create idealized (unfailing) link for test purposes
    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                                      'protocols': ['TCP', 'UDP', 'FTP', 'HTTP', 'HTTPS', 'MODBUS-TCP'],
                                      'mtbf_h': 0, 'mttr_h': 0},
                           name='ideal_link', element='link', overwrite=False, check_required=True)

    connections = []

    # iterate over independent paths
    for i in range(n):
        # create source, target devs on path
        s_dev, s_app = pi.create_ict_devapp(net, name=f'S{i}', device_type=DEV_TYPE, app_type=APP_TYPE)
        t_dev, t_app = pi.create_ict_devapp(net, name=f'T{i}', device_type=DEV_TYPE, app_type=APP_TYPE)

        # create nodes on path
        nodes = []
        for j in range(m):
            node = pi.create_ict_node(net, name=f'N{i}{j}', node_type=NODE_TYPE, link_types=['ideal_link'], 
                                     mtbf_h=mtbf_h, mttr_h=mttr_h)

            nodes.append(node)

        
        # build list of path
        chain = [s_dev] + nodes + [t_dev]

        # connect all nodes
        for u, v in zip(chain[:-1], chain[1:]):
            u_name = net[u[0]].loc[u[1], 'name']
            v_name = net[v[0]].loc[v[1], 'name']
            pi.create_ict_link(net, from_elt=u, to_elt=v, name=f'{u_name}-{v_name}', link_type='ideal_link')

        conn = pi.create_ict_connection(net, name=f'conn {i}', from_app=s_app, to_app=t_app, protocol='TCP')

        connections.append(conn)

    return net, connections