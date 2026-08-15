from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Circle, Ellipse, Rectangle, RegularPolygon, Arc
import numpy as np
import re
import ast
import pandapower.plotting as plot
import matplotlib
from pandas import isnull, Series, DataFrame
from pandapower.plotting.collections import (
    add_cmap_to_collection, 
    # _get_coords_from_geojson
)
from pandapower.plotting.plotting_toolbox import (
    get_index_array, 
    coords_from_node_geodata,
)


def _get_coords_from_geojson(gj_str):
    matches = [f"{gj_str['coordinates']}"]

    if not matches:
        return None
    if len(matches) > 1:
        raise ValueError("More than one match found in GeoJSON string")
    for m in matches:
        return ast.literal_eval(m)
    return None

def _rotate_dim2(arr, ang):
    """
    :param arr: array with 2 dimensions
    :param ang: angle [rad]
    """
    return np.dot(np.array([[np.cos(ang), np.sin(ang)], [-np.sin(ang), np.cos(ang)]]), arr)


def create_ict_node_collection(
    ict_net, nodes=None, size=1, color=None, z=None, cmap=None, norm=None,
    infofunc=None, picker=False, node_geodata=None, cbar_title="Node Value",
    clim=None, plot_colormap=True, **kwargs
):
    """Create a matplotlib patch collection for nodes in a pandaict network."""
    nodes = get_index_array(nodes, ict_net.node.index)
    if len(nodes) == 0:
        return None

    if node_geodata is None:
        node_geodata = ict_net["node"].geodata.apply(_get_coords_from_geojson)

    nodes_with_geodata = nodes[np.isin(nodes, node_geodata.index.values)]
    coords = node_geodata.loc[nodes_with_geodata].values

    if len(nodes_with_geodata) == 0:
        return None

    if "height" not in kwargs and "width" not in kwargs:
        kwargs["height"] = kwargs["width"] = 2 * size

    angle = kwargs.pop("angle", 0)
    patches = [
        Ellipse((x, y), angle=angle, **kwargs) for x, y in coords
    ]
    pc = PatchCollection(patches, match_original=True, picker=picker)
    pc.node_indices = np.array(nodes_with_geodata)
    pc.info = (
        [infofunc(node) for node in nodes_with_geodata]
        if infofunc is not None else []
    )
    pc.patch_type = "ellipse"
    pc.size = size

    if "zorder" in kwargs:
        pc.set_zorder(kwargs["zorder"])

    if cmap is not None:
        if z is None:
            raise ValueError(
                "z must be provided when using a colormap for ICT nodes."
            )
        z = np.asarray(z)
        if len(z) == len(nodes):
            z = z[valid_coords.to_numpy()]
        elif len(z) != len(nodes_with_geodata):
            raise ValueError(
                "z must have one value for each selected ICT node."
            )
        add_cmap_to_collection(
            pc, cmap, norm, z, cbar_title, plot_colormap, clim
        )

    return pc


def create_ict_link_collection(
        ict_net, links=None, link_table="link", link_geodata: DataFrame or None = None,
        use_node_geodata=True, cmap: 'Colormap' = None, **kwargs):
    links = ict_net.link.index.tolist() if links is None else links
    if len(links) == 0:
        return None

    data = []
    if use_node_geodata:
        node_geodata = ict_net["node"].geodata.apply(_get_coords_from_geojson)
        for link, (a, b) in ict_net.link.loc[links, ["from", "to"]].iterrows():
            # if a in node_geodata.index.values and b in node_geodata.index.values:
            if a[0] == "node" and a[1] in node_geodata.index.values and b[0][0] == "node" and b[0][1] in node_geodata.index.values:
                # data.append(([(node_geodata.at[a[1], "x"], node_geodata.at[a[1], "y"]),
                #               (node_geodata.at[b[0][1], "x"], node_geodata.at[b[0][1], "y"])]))
                data.append(([(node_geodata[a[1]][0], node_geodata[a[1]][1]),
                              (node_geodata[b[0][1]][0], node_geodata[b[0][1]][1])]))
    else:
        link_geodata = ict_net["link_geodata"]
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
        device_node = ict_net.link.loc[ict_net.link["from"] == ("device", i), "to"]
        p1 = ict_net.node_geodata[["x", "y"]].loc[device_node.values[0][0][1]]
        p2 = p1 + _rotate_dim2(np.array([0, size]), orientation)
        polys.append(Rectangle([p2[0] - size / 2, p2[1] - size / 2], size, size))
        lines.append((p1, p2 - _rotate_dim2(np.array([0, size / 2]), orientation)))
        if infofunc is not None:
            infos.append(infofunc(i))
    device1 = PatchCollection(polys,
                              picker=picker, color=color, **kwargs)
    device2 = LineCollection(lines, picker=picker, color=color, **kwargs)
    device1.info = infos
    device2.info = infos
    return device1, device2


def create_ict_connection_collection(
    ict_net, conns=None, use_node_geodata=True, size=1.0, orientation=0, **kwargs
):
    conns = ict_net.conn.index.tolist() if conns is None else conns
    if len(conns) == 0:
        return None

    data = []
    if use_node_geodata:
        node_geodata = ict_net["node_geodata"]
        for conn, (a, b) in ict_net.conn.loc[conns, ["from", "to"]].iterrows():
            # if a in node_geodata.index.values and b in node_geodata.index.values:
            node_a = ict_net.link.loc[
                ict_net.link["from"] == ("device", ict_net.app.iloc[a].loc["device"]),
                "to",
            ].item()[0]
            node_b = ict_net.link.loc[
                ict_net.link["from"] == ("device", ict_net.app.iloc[b].loc["device"]),
                "to",
            ].item()[0]
            if (
                node_a[0] == "node"
                and node_a[1] in node_geodata.index.values
                and node_b[0] == "node"
                and node_b[1] in node_geodata.index.values
            ):
                device_center_a = ict_net.node_geodata.loc[node_a[1]]
                device_center_b = ict_net.node_geodata.loc[node_b[1]]
                data.append(
                    (
                        [
                            tuple(
                                (device_center_a["x"], device_center_a["y"])
                                + _rotate_dim2(np.array([0, size]), orientation)
                            ),
                            tuple(
                                (device_center_b["x"], device_center_b["y"])
                                + _rotate_dim2(np.array([0, size]), orientation)
                            ),
                        ]
                    )
                )
    else:
        conn_geodata = ict_net["conn_geodata"]
        for conn in conns:
            if conn in conn_geodata.index.values:
                data.append((conn_geodata.loc[conn, "coords"]))

    oc = LineCollection(data, **kwargs)
    return oc
