import numpy as np


def pandas_to_dict(index, data):
    return {idx: val for idx, val in zip(index, data)}


def shift_geodata(net, offset):
    """
    Shifts node and link geodata by the given offset

    Parameters
    ----------
    net : pandaict net
    offset : 2D numpy.array
        Offset by which all geocoordinates will be shifted

    Examples
    --------
    >>> shift_geodata(net, numpy.array([0.1, 0.1]))
    """

    if not len(net.node_geodata):
        print("No node_geodata found, skipping..")
    else:
        for i, geo in net.node_geodata.iterrows():
            net.node_geodata.loc[i, ["x", "y"]] = np.array(
                [geo.x, geo.y]) + offset

    if not len(net.link_geodata):
        print("No link_geodata found, skipping..")
    else:
        for i, geo in net.link_geodata.iterrows():
            net.link_geodata.loc[i, "coords"] = [
                (np.array([x, y]) + offset).tolist() for x, y in geo.coords
            ]
