from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Circle, Ellipse, Rectangle, RegularPolygon, Arc
import numpy as np
import pandapower.plotting as plot
import matplotlib


def _rotate_dim2(arr, ang):
    """
    :param arr: array with 2 dimensions
    :param ang: angle [rad]
    """
    return np.dot(np.array([[np.cos(ang), np.sin(ang)], [-np.sin(ang), np.cos(ang)]]), arr)


def create_ict_node_collection(ict_net, nodes=None, node_geodata=None, size=1, **kwargs):
    nodes = ict_net.node.index.tolist() if nodes is None else nodes
    if len(nodes) == 0:
        return None

    if node_geodata is None:
        node_geodata = ict_net["node_geodata"]

    coords = zip(node_geodata.loc[nodes, "x"].values, node_geodata.loc[nodes, "y"].values)

    if 'height' not in kwargs and 'width' not in kwargs:
        kwargs['height'] = kwargs['width'] = 2 * size

    def figmaker(x, y, i):
        angle = kwargs['angle'] if 'angle' in kwargs else 0
        fig = Ellipse((x, y), angle=angle, **kwargs)
        return fig

    patches = [figmaker(x, y, i) for i, (x, y) in enumerate(coords) if x != np.nan]
    pc = PatchCollection(patches, match_original=True)

    if "zorder" in kwargs:
        pc.set_zorder(kwargs["zorder"])
    return pc


def create_ict_link_collection(ict_net, links=None, use_node_geodata=True, **kwargs):
    links = ict_net.link.index.tolist() if links is None else links
    if len(links) == 0:
        return None

    node_geodata = ict_net["node_geodata"]
    link_geodata = ict_net["link_geodata"]

    data = []
    if use_node_geodata:
        for link, (a, b) in ict_net.link.loc[links, ["from_node", "to_node"]].iterrows():
            if a in node_geodata.index.values and b in node_geodata.index.values:
                data.append(([(node_geodata.at[a, "x"], node_geodata.at[a, "y"]),
                              (node_geodata.at[b, "x"], node_geodata.at[b, "y"])]))
    else:
        for link in links:
            if link in link_geodata.index.values:
                data.append((link_geodata.loc[link, "coords"]))

    lc = LineCollection(data, **kwargs)
    return lc


def create_ict_device_collection(ict_net, size=1., infofunc=None, orientation=0,
                                 picker=False, **kwargs):
    """
    Creates a matplotlib patch collection of pandaict server.

    Input:
        **ict_net** (pandaictNet) - The pandaict network

    OPTIONAL:
        **size** (float, 1) - patch size

        **infofunc** (function, None) - infofunction for the patch element

        **orientation** (float, 0) - orientation of load collection. 0 is directed upwards,
            increasing values lead to clockwise direction changes.

        **picker** (bool, False) - picker argument passed to the patch collection

        **kwargs - key word arguments are passed to the patch function

    OUTPUT:
        **server1** - patch collection

        **server2** - patch collection
    """
    lines = []
    polys = []
    infos = []
    color = kwargs.pop("color", "k")
    for i, device in ict_net.device.iterrows():
        p1 = ict_net.node_geodata[["x", "y"]].loc[device.node]
        p2 = p1 + _rotate_dim2(np.array([0, size]), orientation)
        polys.append(Rectangle([p2.iloc[0] - size / 2, p2.iloc[1] - size / 2], size, size))
        lines.append((p1, p2 - _rotate_dim2(np.array([0, size / 2]), orientation)))
        if infofunc is not None:
            infos.append(infofunc(i))
    device1 = PatchCollection(polys,
            picker=picker, **kwargs)
    device2 = LineCollection(lines, picker=picker, **kwargs)
    device1.info = infos
    device2.info = infos
    return device1, device2









