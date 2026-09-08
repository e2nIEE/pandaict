'''
Created on 18.08.2026
@author: fnuetz

SPDX-FileCopyrightText: 2026 Fabian Nuetz <fabian.nuetz@iee.fraunhofer.de>
SPDX-License-Identifier: BSD-3-Clause
'''

import numpy as np
import matplotlib.colors as mcolors
import networkx as nx



def _build_criticality_colors(scores, cmap, colormap, highlight_color):
    """Map criticality scores to colors via diverging colormap or binary mode.

    Returns (colors, norm) where norm is the TwoSlopeNorm for the colorbar
    or None in binary mode.
    """
    scores = np.array(scores)

    if cmap:
        max_deviation = max(abs(scores.max() - 1), abs(scores.min() - 1))
        norm = mcolors.TwoSlopeNorm(vmin=1 - max_deviation, vcenter=1,
                                    vmax=1 + max_deviation)
        colors = [colormap(norm(c)) for c in scores]
        return colors, norm

    colors = [highlight_color if c > 1 else 'black' for c in scores]
    return colors, None

def _auto_highlight(scores, elements):
    """Return indices of elements whose criticality score exceeds 1."""
    mask = np.array(scores) > 1
    return [e for e, m in zip(elements, mask) if m]

def _draw_directed_edges(nxg, pos, ax, edge_colors, edge_width=2,
                         highlight_edges=None, rad=0.15):
    """Draw edges of a MultiDiGraph with direction arrows.

    Unidirectional edges are drawn as straight arrows.
    Bidirectional edges (both A->B and B->A exist) are drawn as curved
    arrows so both directions are visible.
    """
    highlight_set = set(tuple(e) for e in (highlight_edges or []))

    for idx, (u, v, data) in enumerate(nxg.edges(data=True)):
        color = edge_colors[idx]
        has_reverse = nxg.has_edge(v, u)
        is_highlight = (u, v) in highlight_set

        if has_reverse and u != v:
            connectionstyle = f"arc3,rad={rad}"
        else:
            connectionstyle = "arc3,rad=0"

        nx.draw_networkx_edges(
            nxg, pos, ax=ax,
            edgelist=[(u, v)],
            edge_color=[color],
            width=edge_width * 1.8 if is_highlight else edge_width,
            arrows=True,
            arrowsize=18,
            connectionstyle=connectionstyle,
            min_source_margin=8,
            min_target_margin=8,
        ) 