'''
Created on 09.02.2026
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

import networkx as nx
import numpy as np

from pandaict.topology.routing          import __modify_multidigraph_by_iptables
from pandaict.topology.routing_utils    import create_multidigraph, __get_nx_node_for_elt
from pandaict.reliability.monte_carlo import (
    estimate_mttf_mttr,
    analyze_critical_components as _analyze_critical_components,
    empirical_reliability as _empirical_reliability
)
from pandaict.reliability.monte_carlo_helpers import _critical_bar_plot
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from pandaict.reliability.reliability_utils import _get_lam_mu_from_graph


def _pandaict_to_mcnxgraph(ict_net, connections, downstream=True, respect_iptables=False):
    """
    Build a NetworkX MultiDiGraph from a pandaict net and extract
    source/target node lists from the given connections.

    :INPUT:
        **ict_net**           - pandaict ICT-Network object
        **connections**       - list of connections in pandaict element notation ('conn', index)
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
        conn_data = ict_net['conn'].loc[ind]

        # Check protocol consistency
        if conn_data['protocol'] != protocol:
            raise ValueError('Protocols of connections must be identical.')

        from_dev = ('device', ict_net.app.loc[conn_data['from']]['device'])
        to_dev   = ('device', ict_net.app.loc[conn_data['to']]['device'])

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


def plot_graph(ict_net, protocol='TCP',
               highlight_nodes=None, highlight_edges=None,
               edge_criticality=None, node_criticality=None,
               default_color='lightblue', highlight_color='red',
               cmap=True, show_colorbar=True, seed=8):
    """
    Plot a pandaict network as a graph with optional criticality-based color encoding.
    Converts the given pandaict network into a NetworkX MultiDiGraph and renders it
    using a spring layout. When criticality scores are provided, components are
    color-coded using a diverging colormap centered at 1 (expected criticality),
    making it easy to visually identify over- and under-critical components.

    :INPUT:
        **ict_net** (pandaict.ICTNetwork) - pandaict network object to be plotted.

        **protocol** (str, default 'TCP') - Communication protocol used to build the
        underlying MultiDiGraph.

        **highlight_nodes** (list or None, default None) - List of node indices to
        highlight. If None and node_criticality is provided, nodes with a score > 1
        are highlighted automatically.

        **highlight_edges** (list of tuple or None, default None) - List of edge tuples
        to highlight. If None and edge_criticality is provided, edges with a score > 1
        are highlighted automatically.

        **edge_criticality** (array-like or None, default None) - Criticality scores
        per edge as returned by :func:`analyze_critical_components_for_conn`. When
        provided, edges are colored according to their score.

        **node_criticality** (array-like or None, default None) - Criticality scores
        per node as returned by :func:`analyze_critical_components_for_conn`. When
        provided, nodes are colored according to their score.

        **default_color** (str, default 'lightblue') - Node fill color when no
        criticality scores are provided.

        **highlight_color** (str, default 'red') - Color used for critical components
        when cmap is False (binary mode).

        **cmap** (bool, default True) - If True, use a diverging colormap
        (light gray -> black -> red) centered at 1. If False, use binary coloring:
        red if score > 1, black otherwise.

        **show_colorbar** (bool, default True) - If True and cmap is True, display a
        colorbar indicating the criticality scale. A dashed white line marks the
        expected value of 1.

        **seed** (int, default 8) - Random seed for the spring layout, ensuring
        reproducible node positions.

    :OUTPUT:
        None. Displays the plot via matplotlib.

    .. note::
        The criticality scores can be obtained from
        :func:`analyze_critical_components_for_conn`. A score of 1 means the
        component fails exactly as often as expected. Scores above 1 indicate
        disproportionately critical components (colored towards red), while
        scores below 1 indicate less critical components (colored towards
        light gray).

    :EXAMPLE:
        Basic network plot without criticality:

        >>> plot_graph(net)

        Plot with criticality color encoding from a previous analysis:

        >>> result = analyze_critical_components_for_conn(
        ...     net, [conn_a], plot=False)
        >>> plot_graph(net,
        ...            edge_criticality=result['edge_criticality'],
        ...            node_criticality=result['node_criticality'])

        Binary highlighting (no colormap):

        >>> plot_graph(net,
        ...            edge_criticality=result['edge_criticality'],
        ...            node_criticality=result['node_criticality'],
        ...            cmap=False)
    """
    # TODO: Fix plot for unidirectional graphs
    # Build multidigraph once
    G = create_multidigraph(ict_net, protocol, validate=True)

    # Build label mapping: node index -> device/node name
    labels = {}
    for n, attr in G.nodes(data=True):
        elt_type, elt_idx = attr['pielt']
        labels[n] = ict_net[elt_type].loc[elt_idx]['name']

    for u, v, key, data in G.edges(data=True, keys=True):
        G[u][v][key]['weight'] = 1.0

    # Custom diverging colormap: light gray -> black -> red
    colors = ['lightgray', 'black', 'red']
    colormap = mcolors.LinearSegmentedColormap.from_list('criticality', colors)

    norm = None

    # --- Handle edge criticality ---
    if edge_criticality is not None:
        edge_criticality = np.array(edge_criticality)

        if cmap:
            # Diverging colormap mode
            max_deviation = max(abs(edge_criticality.max() - 1),
                                abs(edge_criticality.min() - 1))
            vmin = 1 - max_deviation
            vmax = 1 + max_deviation

            norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=1, vmax=vmax)
            edge_colors = [colormap(norm(c)) for c in edge_criticality]
        else:
            # Binary mode: red if > 1, black otherwise
            edge_colors = [highlight_color if c > 1 else 'black' for c in edge_criticality]

        # Determine highlight edges based on criticality > 1
        critical_edges_mask = edge_criticality > 1
        edges_array = np.array(list(G.edges()))
        critical_edges = [tuple(e) for e in edges_array[critical_edges_mask]]
        highlight_edges = critical_edges if highlight_edges is None else highlight_edges
    else:
        edge_colors = ['gray' for _ in G.edges()]

    # --- Handle node criticality ---
    if node_criticality is not None:
        node_criticality = np.array(node_criticality)

        if cmap:
            # Diverging colormap mode
            max_deviation = max(abs(node_criticality.max() - 1),
                                abs(node_criticality.min() - 1))
            vmin = 1 - max_deviation
            vmax = 1 + max_deviation

            node_norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=1, vmax=vmax)
            node_colors = [colormap(node_norm(c)) for c in node_criticality]

            if norm is None:
                norm = node_norm
        else:
            # Binary mode: red if > 1, black otherwise
            node_colors = [highlight_color if c > 1 else 'black' for c in node_criticality]

        # Determine highlight nodes based on criticality > 1
        critical_nodes_mask = node_criticality > 1
        nodes_array = np.array(list(G.nodes()))
        critical_nodes = list(nodes_array[critical_nodes_mask])
        highlight_nodes = critical_nodes if highlight_nodes is None else highlight_nodes
    else:
        node_colors = [default_color for _ in G.nodes()]

    highlight_nodes = highlight_nodes or []
    highlight_edges = highlight_edges or []

    # --- Draw ---
    fig, ax = plt.subplots(figsize=(5,5))
    pos = nx.spring_layout(G, seed=seed)

    nx.draw(G, pos, ax=ax,
            node_color=node_colors,
            edge_color=edge_colors,
            with_labels=True,
            labels=labels,
            font_color='black',
            node_size=500,
            font_size=12,
            width=2)

    # Add colorbar (only in cmap mode)
    if show_colorbar and cmap and norm is not None:
        sm = plt.cm.ScalarMappable(cmap=colormap, norm=norm)
        sm.set_array([])
        cbar = plt.colorbar(sm, ax=ax, shrink=0.8)
        cbar.set_label('Criticality Score', fontsize=12)
        cbar.ax.axhline(y=1, color='white', linewidth=2, linestyle='--')

    plt.tight_layout()
    plt.show()


def estimate_mtbf_mttr_for_conn(ict_net, connections, **kwargs):
    """
    Estimate **MTBF**, **MTTF** and **MTTR** for one or more pandaict connections.
    Runs a Monte-Carlo simulation on the given network and connections
    and returns the **Mean Time Between Failures** (MTBF = MTTF + MTTR)
    together with the **Mean Time To Failure** (MTTF) and **Mean Time To Repair** (MTTR).

    :INPUT:
        **ict_net** (pandaict.ICTNetwork) - pandaict network object containing
        topology and component reliability attributes (mtbf_h, mttr_h).

        **connections** (list of tuple) - One or more connection(s) in pandaict 
        element notation. 
        
    :OUTPUT:
        **result** (dict) - Dictionary with the following keys:
                
        - mtbf_h (float) - Mean Time Between Failures in hours (MTBF = MTTF + MTTR). 
        
        - mttf_h (float) - Mean Time To Failure in hours. 
        
        - mttr_h (float) - Mean Time To Repair in hours. Returns numpy.inf if the system is non-repairable.

    .. note::
        This function shares optional keyword arguments with
        :func:`analyze_critical_components_for_conn` and
        :func:`empirical_reliability_function`.
        See :ref:`mc_kwargs` for the full list.

    :EXAMPLE:
        >>> result = estimate_mtbf_mttr_for_conn(net, [conn_a], N=100_000)
        >>> print(f"MTBF = {result['mtbf_h']:.1f} h, MTTR = {result['mttr_h']:.1f} h")
        MTBF = 9200.4 h, MTTR = 5.8 h
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

    if config.get('max_time') < np.inf:
        print('Info: max_time Speedup is used. MTTF, MTTR might be meaningless.')

    # get networkX graph and source/target lists
    graph, sources, targets = _pandaict_to_mcnxgraph(ict_net, connections)

    # run monte-carlo, get mttf, mttr
    res = estimate_mttf_mttr(graph, sources, targets, **config)

    # mttf -> mtbf
    mttr = 0 if np.isinf(res['mttr']) else res['mttr']
    mttf = res['mttf']

    mtbf = mttf + mttr

    return {'mtbf_h': mtbf,
            'mttf_h': mttf,
            'mttr_h': res['mttr'],
            'samples': res.get('mttf_samples')}


def analyze_critical_components_for_conn(ict_net, connections,
                                         top_n=-1, plot=True, verbose=True,
                                         rate_adjustment=True, save_excel=False,
                                         **kwargs):
    """
    Identify disproportionately critical components for pandaict connections.
    Runs a Monte-Carlo simulation with critical-component tracking enabled and
    computes per-component criticality scores. A score greater than 1 means the
    component causes system failures more often than its reliability rates alone 
    would predict. Both failure and repair events are tracked separately.

    :INPUT:
        **ict_net** (pandaictNet) - pandaict network containing
        topology and component reliability attributes.

        **connections** (list of tuple) - One or more connection(s) in pandaict 
        element notation.

    :OPTIONAL:
    
        **top_n** (int, default -1) - Number of most critical components to display.
        -1 shows all components.

        **plot** (bool, default True) - If True, produce a horizontal bar chart of
        criticality scores for edges and nodes.

        **verbose** (bool, default True) - If True, print the ranked criticality
        table to the console.

        **rate_adjustment** (bool, default True) - If True, normalise observed counts
        by expected event rates, yielding a topological criticality independent of
        absolute failure/repair rates. If False, report raw counts.

        **save_excel** (bool, default False) - If True, export the analysis results
        to an Excel file in the current working directory.

    :OUTPUT:
        **result** (dict) - Dictionary with the following keys:

        - edge_criticality (np.ndarray or None) - Failure criticality score per edge.

        - node_criticality (np.ndarray or None) - Failure criticality score per node.

        - edge_repair_criticality (np.ndarray or None) - Repair criticality score per edge.

        - node_repair_criticality (np.ndarray or None) - Repair criticality score per node.

    .. note::
        **Relation to classical importance measures**

        The criticality score is conceptually related to classical component
        importance measures from reliability theory:

        - With ``rate_adjustment=True``, the score reflects *structural importance*:
          how much more often a component triggers a system failure than its
          failure rate alone would predict. This is closely related to the
          **Birnbaum importance measure**, which expresses the probability that
          the system state is determined by a given component.

        - With ``rate_adjustment=False``, the score reflects the raw failure
          frequency of each component, which is closer to the **Criticality
          importance measure** (Birnbaum x component unreliability).

        Empirical comparisons across various network topologies show that the
        ranking produced by this function correlates well with Birnbaum
        importance (mean Spearman: 0.76), making it a practical
        simulation-based alternative when analytical importance measures are
        difficult to compute.

    .. note::
        This function shares optional keyword arguments with
        :func:`estimate_mtbf_mttr_for_conn` and
        :func:`empirical_reliability_function`.
        See :ref:`mc_kwargs` for the full list.

    :EXAMPLE:
        >>> result = analyze_critical_components_for_conn(
        ...     net, [conn_a], plot=False)
        >>> result['edge_criticality'][:3]
        array([1.42, 0.87, 1.15])
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
            'edge_repair_criticality': None,
            'node_repair_criticality': None,
            'edge_names': None,
            'node_names': None,
            'edge_elements': None,
            'node_elements': None,
        }

    # Extract rates from the annotated graph
    lam_edges, lam_nodes, mu_edges, mu_nodes = _get_lam_mu_from_graph(graph)

    # Build name/element-maps
    edge_names, edge_elements, node_names, node_elements = {}, {}, {}, {}
    for i, (u, v, attr) in enumerate(graph.edges(data=True)):
        elt_type, elt_idx = attr['pielt']
        edge_elements[i] = (elt_type, elt_idx)
        edge_names[i] = ict_net[elt_type].iloc[elt_idx]['name']

    for i, (n, attr) in enumerate(graph.nodes(data=True)):
        elt_type, elt_idx = attr['pielt']
        node_elements[i] = (elt_type, elt_idx)
        node_names[i] = ict_net[elt_type].iloc[elt_idx]['name']


    # Run the full analysis with the caller's display/analysis settings
    crit_result = _analyze_critical_components(
        all_critical, graph, sources, targets,
        lam_edges, lam_nodes, mu_edges, mu_nodes,
        top_n=top_n,
        plot=plot,
        verbose=verbose,
        rate_adjustment=rate_adjustment,
        save_excel=save_excel,
        edge_labels=edge_names,
        node_labels=node_names
    )

    if crit_result is None:
        return {
            'edge_criticality': None,
            'node_criticality': None,
            'edge_repair_criticality': None,
            'node_repair_criticality': None,
            'edge_names': None,
            'node_names': None,
            'edge_elements': None,
            'node_elements': None,
        }
    
    if plot:

        edge_crit = crit_result['edge_criticality'] # + crit_result['edge_repair_criticality'] TODO: add later
        node_crit = crit_result['node_criticality'] # + crit_result['node_repair_criticality'] TODO: add later
        
        top_edge_fail_idx = np.argsort(edge_crit)[::-1]
        top_node_fail_idx = np.argsort(node_crit)[::-1]

        _critical_bar_plot(top_edge_fail_idx, top_node_fail_idx,
                           edge_crit, edge_names,
                           node_crit, node_names,
                           rate_adjustment)

    return {
        'edge_criticality': crit_result['edge_criticality'],
        'node_criticality': crit_result['node_criticality'],
        'edge_repair_criticality': crit_result['edge_repair_criticality'],
        'node_repair_criticality': crit_result['node_repair_criticality'],
        'edge_names': [edge_names[i] for i in range(len(edge_names))],
        'node_names': [node_names[i] for i in range(len(node_names))],
        'edge_elements': [edge_elements[i] for i in range(len(edge_elements))],
        'node_elements': [node_elements[i] for i in range(len(node_elements))],
    }


def empirical_reliability_function(ict_net, connections, T, **kwargs):
    """
    Estimate the reliability function R(T) for pandaict connections,
    which describes the likelihood of system level survival longer that T.
    Approximates R(T) = P(system lifetime > T) by generating first-failure-time
    samples via Monte-Carlo simulation and computing the empirical survival
    fraction at one or more time points.

    :INPUT:
         **ict_net** (pandaictNet) - pandaict network containing
        topology and component reliability attributes.

        **connections** (list of tuple) - One or more connection(s) in pandaict 
        element notation.    

        **T** (float or array-like of float) - Time point(s) in hours at which the
        reliability is evaluated. A scalar input returns a scalar; an array returns
        an array of the same length.

    :OUTPUT:
        **R(T)** (float or np.ndarray) - If T is scalar, the reliability value R(T) in [0, 1]. \
        If T is array-like, element-wise reliability values of the same length as T.

        Returns None if the simulation produced no valid samples.

    .. note::
        This function shares optional keyword arguments with
        :func:`estimate_mtbf_mttr_for_conn` and
        :func:`analyze_critical_components_for_conn`.
        See :ref:`mc_kwargs` for the full list.

    :EXAMPLE:
        Scalar evaluation:

        >>> R = empirical_reliability_function(net, [conn_a], T=8760)
        >>> print(f"R(1 year) = {R:.4f}")
        R(1 year) = 0.6321

        Vectorised evaluation over a time axis:

        >>> import numpy as np
        >>> T = np.linspace(0, 50_000, 200)
        >>> R = empirical_reliability_function(net, [conn_a], T=T, N=500_000)
        >>> R.shape
        (200,)
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

    R = np.array([_empirical_reliability(t, samples) for t in T_arr])

    return float(R[0]) if scalar_input else R