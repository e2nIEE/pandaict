from pandapower.auxiliary import get_free_id, _preserve_dtypes
from pandaict_orig.auxiliary import pandaictNet
from numpy import dtype, zeros
import pandas as pd


def create_empty_ict_network():

    net = pandaictNet({
        "node": [
            ("name", dtype(object)),
            ("type", dtype(object)),
            ("in_service", "bool")
            ],
        "link": [
            ("name", dtype(object)),
            ("from_node", "i8"),
            ("to_node", "i8"),
            ("length_km", "f8"),
            ("type", dtype(object)),
            ("protocols", dtype(object)),
            ("in_service", 'bool')
            ],
        "device": [
            ("name", dtype(object)),
            ("node", "i8"),
            ("type", dtype(object)),
            ("protocol", dtype(object)),
            ("service", "i8"),
            ("interconnects", dtype(object)),
            ("in_service", "bool")
            ],
        "node_geodata": [
            ("x", "f8"),
            ("y", "f8")
            ],
        "link_geodata": [
            ("coords", dtype(object))
            ]
        })

    for s in net:
        if isinstance(net[s], list):
            net[s] = pd.DataFrame(zeros(0, dtype=net[s]), index=[])
    return net


def create_ict_node(net, type=None, name=None, index=None, in_service=True):
    if index is not None and index in net["node"].index:
        raise UserWarning("A node with index %s already exists" % index)

    if index is None:
        index = get_free_id(net["node"])

    dtypes = net.node.dtypes

    net.node.loc[index, ["name", "type", "in_service"]] = [name, type, in_service]

    _preserve_dtypes(net.node, dtypes)

    return index


def create_ict_link(net, from_node, to_node, length_km, protocols, type="wired", name=None,
                    index=None, in_service=True):
    for n in [from_node, to_node]:
        if n not in net["node"].index.values:
            raise UserWarning(
                "Link %s tries to attach to non-existing node %s" % (name, n))

    if index is None:
        index = get_free_id(net["link"])

    if index in net["link"].index:
        raise UserWarning("A link with index %s already exists" % index)

    dtypes = net.link.dtypes

    net.link.loc[index, ["name", "from_node", "to_node", "length_km",
                         "type", "in_service"]] = \
        [name, from_node, to_node, length_km, type, in_service]
    net.link['protocols'] = net.link['protocols'].apply(lambda x: protocols)

    _preserve_dtypes(net.link, dtypes)

    return index


def create_ict_device(net, node, protocol, service, interconnects, name=None, index=None, type=None,
                      in_service=True):
    if index is not None and index in net.device.index:
        raise UserWarning("A device with index %s already exists" % index)

    if index is None:
        index = get_free_id(net.device)

    if node not in net.node.index:
        raise UserWarning(
            "Device tries to connect to unavailable node %s" % node)

    dtypes = net.device.dtypes

    net.device.loc[index, ["name", "node", "service", "type",
                           "interconnects", "in_service"]] = \
        [name, node, service, type, interconnects, in_service]
    net.device['protocol'] = net.device['protocol'].apply(lambda x: protocol)

    _preserve_dtypes(net.device, dtypes)
