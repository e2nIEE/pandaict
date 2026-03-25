'''
Created on 09.02.2026
@author: fnuetz
'''

import networkx as nx
import numpy as np

from pandaict.topology.routing          import __modify_multidigraph_by_iptables
from pandaict.topology.routing_utils    import create_multidigraph, __get_nx_node_for_elt
from pandaict.reliability.monte_carlo   import estimate_mttf_mttr, analyze_critical_components

def _pandaict_to_mcnxgraph(ict_net, connections, downstream=True, respect_iptables=False):
    """build networkX multidigraph object from pandaICT net and source, target lists from connections"""

    sources = []
    targets = []

    # get protocol of first connection
    protocol = ict_net['conn']['protocol'][0]

    # Build multidigraph once
    mdg = create_multidigraph(ict_net, protocol, validate=True)

    for conn in connections:
        ind = conn[1]
        conn = ict_net['conn'].iloc[ind]
        # check if different protocols are used
        if not conn['protocol'] == protocol:
            raise(ValueError, 'protocols of connections must be identical.')

        from_dev = ('device', ict_net.app.iloc[conn['from']]['device'])
        to_dev = ('device', ict_net.app.iloc[conn['to']]['device'])

        if not downstream:
            from_dev, to_dev = to_dev, from_dev

        if respect_iptables:
            __modify_multidigraph_by_iptables(ict_net, mdg, from_dev, to_dev)

        from_nxnode = __get_nx_node_for_elt(mdg, from_dev)
        to_nxnode = __get_nx_node_for_elt(mdg, to_dev)

        for n in mdg.nodes():
            ndata = mdg.nodes(data=True)[n]
            pinode = ndata['pielt']
            mtbf = ict_net[pinode[0]].loc[pinode[1]]['mtbf_h']
            mttr = ict_net[pinode[0]].loc[pinode[1]]['mttr_h']
            ndata.update({'mtbf_h': mtbf, 'mttr_h': mttr})
            nx.set_node_attributes(mdg, {n: ndata})

        for e in mdg.edges():
            edata = mdg.get_edge_data(e[0], e[1])[0]
            piedge = edata['pielt']
            ltype = ict_net.std_types['link'][ict_net[piedge[0]].loc[piedge[1]]['type']]
            mtbf = ltype['mtbf_h']
            mttr = ltype['mttr_h']
            edata.update({'mtbf_h': mtbf, 'mttr_h': mttr})
            nx.set_node_attributes(mdg, {e: edata})

        sources.append(from_nxnode)
        targets.append(to_nxnode)

    return mdg, sources, targets


def estimate_mtbf_mttr_for_conn(ict_net, connections, **kwargs):
    """
        Estimate MTBF (MTTR) for connections.

        :INPUT:
            **ict_net**     - pandaict ICT-Network object
            **connections** - list of pandaict connection object(s)
            **kwargs**      - optional keywords (see pandaict.reliability.monte_carlo for more information)

        :OUTPUT:
            {
            'mttf': mttf,                   - float, mean time to failure
            'mttr': mttr,                   - float, mean time to repair
            'mttf_samples': mttf_samples,   - np.array, time to failure samples
            'mttr_samples': mttr_samples,   - np.array, time to repair samples
            }
    """
    # set default kwargs
    defaults = {
        'min_connected': -1,
        'N': int(1e5),
        'depth': 200,
        'TOL': 0,
        'max_time': np.inf,
        'max_events': -1,
        'return_samples': True,
        'analyze_crit': False,
        'laziness': 0,
        'use_numba': True,
        'parallel': True
    }

    protected = {
        'analyze_crit': False,
    }

    # TODO: overwrite values not permitted for change
    config = {**defaults, **kwargs, **protected}

    # get networkX graph and source/target lists
    graph, sources, targets = _pandaict_to_mcnxgraph(ict_net, connections)

    # run monte-carlo, get mttf, mttr
    res = estimate_mttf_mttr(graph, sources, targets, **config)

    return res


def analyze_critical_components(ict_net, connections, **kwargs):
    """Analyzes the ict_net for components which are critical for its function

    """
    defaults = {
        'min_connected': -1,
        'N': int(1e5),
        'depth': 200,
        'TOL': 0,
        'max_time': np.inf,
        'max_events': -1,
        'laziness': 0,
        'use_numba': True,
        'parallel': True
    }

    protected = {
        'analyze_crit': True,
        'return_samples': False,
    }

    config = {**defaults, **kwargs, **protected}

    graph, sources, targets = _pandaict_to_mcnxgraph(ict_net, connections)

    res = estimate_mttf_mttr(graph, sources, targets, **config)

    analyze_critical_components(all_critical, G, sources, targets,
                                lam_edges, lam_nodes,
                                mu_edges, mu_nodes,
                                top_n=-1, plot=True, verbose=False, rate_adjustment=True)

    if config['plot_graph']:
        # TODO: plot graph showing critical components
        print('Plotting graph')


    return {
        'edge_criticality': res['edge_criticality'],
        'node_criticality': res['node_criticality']
    }

def approximate_reliability_function(ict_net, connections, T, **kwargs):
    """Approximate the reliability function evaluated in T (R(T) = P(t>T))

    :INPUT:
        **ict_net**     - pandaict ICT-Network object
        **connections** - list of pandaict connection objects
        **T**           - float,

    :OUTPUT:
        **R(T)**        - float, probability that the system lives longer than T
    """
    defaults = {
        'min_connected': -1,
        'N': int(1e5),
        'depth': 200,
        'TOL': 0,
        'max_time': np.inf,
        'max_events': -1,
        'laziness': 0,
        'use_numba': True,
        'parallel': True
    }

    protected = {
        'analyze_crit': True,
        'return_samples': False,
    }

    config = {**defaults, **kwargs, **protected}