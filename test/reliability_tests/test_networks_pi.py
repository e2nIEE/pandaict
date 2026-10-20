'''
Created on 29.07.2026
@author: fnuetz
'''
import pandaict as pi

DEV_TYPE = None     # DeviceType.SERVER
APP_TYPE = None     # AppType.WEBSERVER
NODE_TYPE = None    # NodeType.ROUTER


def _link_chain(net, chain):
    """Connect consecutive elements of *chain* with ideal links."""
    for u, v in zip(chain[:-1], chain[1:]):
        u_name = net[u[0]].loc[u[1], 'name']
        v_name = net[v[0]].loc[v[1], 'name']
        pi.create_ict_link(net, from_elt=u, to_elt=v,
                           name=f'{u_name}-{v_name}', link_type='ideal_link')

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

def build_series_network_with_rates(mttf_list, mttr_h=0.0):
    """
    Pure serial chain of K = len(mttf_list) path nodes with per-node MTTF.
    Only the path nodes can fail; links and devices are ideal.

    Topology: one source/target pair connected through K series nodes.
    System is UP iff all K nodes are up (min_connected = -1).

    :INPUT:
        mttf_list  - list of K per-node MTTF values [h] (only path nodes fail)
        mttr_h     - per-node MTTR [h]; 0.0 => non-repairable

    :OUTPUT:
        (ict_net, connections, node_names)
        node_names - list of the K path-node names in mttf_list order, so the
                     caller can map criticality scores back to reference indices.
    """
    net = pi.create_empty_network(name=f'serial_test_network')

    # create idealized (unfailing) link for test purposes
    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                                      'protocols': ['TCP', 'UDP', 'FTP', 'HTTP', 'HTTPS', 'MODBUS-TCP'],
                                      'mtbf_h': 0, 'mttr_h': 0},
                           name='ideal_link', element='link', overwrite=False, check_required=True)

    mtbf_h = [t + mttr_h for t in mttf_list]

    s_dev, s_app = pi.create_ict_devapp(net, name='S', device_type=DEV_TYPE, app_type=APP_TYPE)
    t_dev, t_app = pi.create_ict_devapp(net, name='T', device_type=DEV_TYPE, app_type=APP_TYPE)

    node_names = []
    nodes = []
    for j, (bf, tr) in enumerate(zip(mtbf_h, [mttr_h] * len(mttf_list))):
        node = pi.create_ict_node(net, name=f'N{j}', node_type=NODE_TYPE,
                                  link_types=['ideal_link'], mtbf_h=bf, mttr_h=tr)
        nodes.append(node)
        node_names.append(net['node'].loc[node[1], 'name'])

    _link_chain(net, [s_dev] + nodes + [t_dev])

    conn = pi.create_ict_connection(net, name='conn', from_app=s_app,
                                    to_app=t_app, protocol='TCP')

    return net, [conn], node_names


def build_parallel_network_with_rates(mttf_list, mttr_h=0.0):
    """
    1-out-of-N parallel redundancy with per-node MTTF.
    N = len(mttf_list) independent single-node paths; only the path nodes can
    fail; links and devices are ideal.

    Topology: N independent source->target paths, each with exactly one
    fallible node. System is UP iff >= 1 path is connected
    (min_connected = 1).

    :INPUT:
        mttf_list  - list of N per-node MTTF values [h] (one node per path)
        mttr_h     - per-node MTTR [h]; 0.0 => non-repairable

    :OUTPUT:
        (ict_net, connections, node_names)
        node_names - list of the N path-node names in mttf_list order.
    """
    net = pi.create_empty_network(name=f'parallel_test_network')

    # create idealized (unfailing) link for test purposes
    pi.create_std_type(net, {'bandwidth_Mbps': (1000, 1000), 'latency_ms': 100, 'wired': True,
                                      'protocols': ['TCP', 'UDP', 'FTP', 'HTTP', 'HTTPS', 'MODBUS-TCP'],
                                      'mtbf_h': 0, 'mttr_h': 0},
                           name='ideal_link', element='link', overwrite=False, check_required=True)

    mtbf_h = [t + mttr_h for t in mttf_list]

    connections = []
    node_names = []
    for i, (bf, tr) in enumerate(zip(mtbf_h, [mttr_h] * len(mttf_list))):
        s_dev, s_app = pi.create_ict_devapp(net, name=f'S{i}',
                                            device_type=DEV_TYPE, app_type=APP_TYPE)
        t_dev, t_app = pi.create_ict_devapp(net, name=f'T{i}',
                                            device_type=DEV_TYPE, app_type=APP_TYPE)

        node = pi.create_ict_node(net, name=f'N{i}', node_type=NODE_TYPE,
                                  link_types=['ideal_link'], mtbf_h=bf, mttr_h=tr)
        node_names.append(net['node'].loc[node[1], 'name'])

        _link_chain(net, [s_dev, node, t_dev])

        connections.append(pi.create_ict_connection(
            net, name=f'conn {i}', from_app=s_app, to_app=t_app, protocol='TCP'))

    return net, connections, node_names