'''
Created on 09.02.2026
@author: fnuetz
'''

import networkx as nx
import numpy as np

from pandaict.topology.routing          import __modify_multidigraph_by_iptables
from pandaict.topology.routing_utils    import create_multidigraph, __get_nx_node_for_elt
from pandaict.reliability.monte_carlo import (
    estimate_mttf_mttr,
    analyze_critical_components as _analyze_critical_components,
    empirical_reliability
)
from pandaict.reliability.reliability_utils import _get_lam_mu_from_graph


def _pandaict_to_mcnxgraph(ict_net, connections, downstream=True, respect_iptables=False):
    """
    Build a NetworkX MultiDiGraph from a pandaICT net and extract
    source/target node lists from the given connections.

    :INPUT:
        **ict_net**           - pandaICT ICT-Network object
        **connections**       - list of pandaICT connection tuples (something, index)
        **downstream**        - bool, direction of connection (default: True)
        **respect_iptables**  - bool, whether to apply iptable modifications (default: False)

    :OUTPUT:
        **mdg**      - NetworkX MultiDiGraph with 'mtbf_h' and 'mttr_h' on all nodes and edges
        **sources**  - list of source node identifiers
        **targets**  - list of target node identifiers
    """
    sources = []
    targets = []

    # Get protocol of first connection
    protocol = ict_net['conn']['protocol'][0]

    # Build multidigraph once
    mdg = create_multidigraph(ict_net, protocol, validate=True)

    for conn_tuple in connections:
        ind = conn_tuple[1]
        conn_data = ict_net['conn'].iloc[ind]

        # Check protocol consistency
        if conn_data['protocol'] != protocol:
            raise ValueError('Protocols of connections must be identical.')

        from_dev = ('device', ict_net.app.iloc[conn_data['from']]['device'])
        to_dev   = ('device', ict_net.app.iloc[conn_data['to']]['device'])

        if not downstream:
            from_dev, to_dev = to_dev, from_dev

        if respect_iptables:
            __modify_multidigraph_by_iptables(ict_net, mdg, from_dev, to_dev)

        from_nxnode = __get_nx_node_for_elt(mdg, from_dev)
        to_nxnode   = __get_nx_node_for_elt(mdg, to_dev)

        sources.append(from_nxnode)
        targets.append(to_nxnode)

    for n in mdg.nodes():
        ndata  = mdg.nodes[n]
        pinode = ndata['pielt']
        mtbf   = ict_net[pinode[0]].loc[pinode[1]]['mtbf_h']
        mttr   = ict_net[pinode[0]].loc[pinode[1]]['mttr_h']
        ndata['mttf_h'] = mtbf - mttr # mttf = mtbf - mttr
        ndata['mttr_h'] = mttr

    for u, v, key, edata in mdg.edges(data=True, keys=True):
        piedge = edata['pielt']
        ltype  = ict_net.std_types['link'][ict_net[piedge[0]].loc[piedge[1]]['type']]
        edata['mttf_h'] = ltype['mtbf_h'] - ltype['mttr_h'] # mttf = mtbf - mttr
        edata['mttr_h'] = ltype['mttr_h']

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

    # overwrite values not permitted for change
    config = {**defaults, **kwargs, **protected}

    # get networkX graph and source/target lists
    graph, sources, targets = _pandaict_to_mcnxgraph(ict_net, connections)

    # run monte-carlo, get mttf, mttr
    res = estimate_mttf_mttr(graph, sources, targets, **config)

    # mttf -> mtbf
    mttr = 0 if np.isinf(res['mttr']) else res['mttr']
    mttf = res['mttf']

    mtbf = mttf + mttr

    return {'mtbf_h': mtbf, 'mttf_h': mttf, 'mttr_h': mttr}


def analyze_critical_components_for_conn(ict_net, connections,
                                         top_n=-1, plot=True, verbose=True,
                                         rate_adjustment=True, save_excel=False,
                                         **kwargs):
    """
    Analyze which network components are disproportionately critical for system reliability.

    Runs a Monte Carlo simulation to collect critical-component data, then calls
    analyze_critical_components with the caller's plot/verbose/rate settings.

    :INPUT:
        **ict_net**           - pandaICT ICT-Network object
        **connections**       - list of pandaICT connection object(s)
        **top_n**             - int, number of top components to display (-1 = all)
        **plot**              - bool, whether to plot criticality bar chart (default: True)
        **verbose**           - bool, whether to print criticality table to console (default: True)
        **rate_adjustment**   - bool, normalize by rates for topological criticality (default: True)
        **kwargs**            - optional keywords forwarded to estimate_mttf_mttr

    :OUTPUT:
        dict with keys:
            'edge_criticality' - np.ndarray, criticality scores per edge
            'node_criticality' - np.ndarray, criticality scores per node
            'full_counts'      - np.ndarray, raw event counts per component
            'total_observed'   - int, total number of system-level transitions observed
            'mttf'             - float, mean time to failure (by-product)
            'mttr'             - float, mean time to repair (by-product)
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
        'parallel': True,
    }

    # Force critical analysis on; samples not needed for the caller
    protected = {
        'analyze_crit': True,
        'return_samples': False,
    }

    config = {**defaults, **kwargs, **protected}

    graph, sources, targets = _pandaict_to_mcnxgraph(ict_net, connections)

    # Run simulation — estimate_mttf_mttr collects all_critical internally
    # (its own analyze call is suppressed via plot=False, verbose=False)
    res = estimate_mttf_mttr(graph, sources, targets, **config)

    mttr = 0 if np.isinf(res['mttr']) else res['mttr']
    mttf = res['mttf']
    mtbf = mttf + mttr

    all_critical = res.get('all_critical')

    # Handle no critical components
    if all_critical is None or (hasattr(all_critical, 'size') and all_critical.size == 0):
        print("Warning: No critical component data collected.")
        return {
            'edge_criticality': None,
            'node_criticality': None,
            'full_counts': None,
            'total_observed': 0,
            'mtbf': res.get('mttf') + res.get('mttr'),
            'mttf': res.get('mttf'),
            'mttr': res.get('mttr'),
        }

    # Extract rates from the annotated graph
    lam_edges, lam_nodes, mu_edges, mu_nodes = _get_lam_mu_from_graph(graph)

    # Run the full analysis with the caller's display/analysis settings
    crit_result = _analyze_critical_components(
        all_critical, graph, sources, targets,
        lam_edges, lam_nodes, mu_edges, mu_nodes,
        top_n=top_n,
        plot=plot,
        verbose=verbose,
        rate_adjustment=rate_adjustment,
        save_excel=save_excel,
    )

    if crit_result is None:
        return {
            'edge_criticality': None,
            'node_criticality': None,
            'full_counts': None,
            'total_observed': 0,
            'mtbf': mtbf,
            'mttf': mttf,
            'mttr': mttr,
        }

    return {
        'edge_criticality': crit_result['edge_criticality'],
        'node_criticality': crit_result['node_criticality'],
        'full_counts': crit_result['full_counts'],
        'total_observed': crit_result['total_observed'],
        'mtbf': mtbf,
        'mttf': mttf,
        'mttr': mttr,
    }


def empirical_reliability_function(ict_net, connections, T, **kwargs):
    """
    Approximate the reliability function R(T) = P(system lifetime > T)
    from Monte Carlo failure-time samples.

    :INPUT:
        **ict_net**           - pandaICT ICT-Network object
        **connections**       - list of pandaICT connection objects
        **T**                 - float or array-like, time point(s) at which R is evaluated
        **kwargs**            - optional keywords

    :OUTPUT:
        If T is scalar:  float    R(T)
    """
    defaults = {
        'min_connected': -1,
        'N': int(1e5),
        'TOL': 0,
        'max_time': np.inf,
        'max_events': -1,
        'laziness': 0,
        'use_numba': True,
        'parallel': True,
    }

    # Samples are required; critical analysis is not.
    # depth=1: each sample must be an individual failure time, not a cycle-averaged mean.
    protected = {
        'return_samples': True,
        'analyze_crit': False,
        'depth': 1,
    }

    config = {**defaults, **kwargs, **protected}

    graph, sources, targets = _pandaict_to_mcnxgraph(ict_net, connections)

    scalar_input = np.isscalar(T)

    if scalar_input:
        # use max_time speedup
        config['max_time'] = T

    res = estimate_mttf_mttr(graph, sources, targets, **config)

    samples = res.get('mttf_samples')

    if samples is None or len(samples) == 0:
        print('Warning: No valid MTTF samples obtained. Cannot estimate R(T).')
        return None

    # Handle scalar and array input uniformly
    T_arr = np.atleast_1d(np.asarray(T, dtype=np.float64))

    R = np.array([empirical_reliability(t, samples) for t in T_arr])

    return float(R[0]) if scalar_input else R