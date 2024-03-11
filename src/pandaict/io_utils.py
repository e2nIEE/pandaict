import pandas as pd
import os
import json
from numpy import int64
import csv
import pandapower as pp 
from pandaict import create_empty_network
import numpy

try:
    import pplog as logging
except ImportError:
    import logging

logger = logging.getLogger(__name__)


def to_json(ict_net, filename=None):
    """
        Saves a pandaict Network in JSON format. The index columns of all pandas DataFrames will
        be saved in ascending order. net elements which name begins with "_" (internal elements)
        will not be saved. Std types will also not be saved.

        INPUT:
            **ict_net** (dict) - The pandaict format network

            **filename** (string or file) - The absolute or relative path to the output file or file-like object

        EXAMPLE:

             >>> pi.to_json(ict_net, "example.json")

    """
    pp.to_json(ict_net, filename)
    return  



def from_json(filename):
    """
    Load a pandaict network from a JSON file.
    The index of the returned network is not necessarily in the same order as the original network.
    Index columns of all pandas DataFrames are sorted in ascending order.

    INPUT:
        **filename** (string or file) - The absolute or relative path to the input file or file-like object

    OUTPUT:
        **convert** (bool) - use the convert format function to

        **ict_net** (dict) - The pandaict format network

    EXAMPLE:

        >>> ict_net = pi.from_json("example.json")

    """

    net = pp.from_json(filename) # the pp function makes a pp network out of this
    # convert into pandaICT
    ict_net = create_empty_network(False)
    ict_net.node = net.node.copy(True)
    ict_net.link = net.link.copy(True)
    ict_net.device = net.device.copy(True)
    ict_net.conn = net.conn.copy(True)
    ict_net.name = net.name
    return ict_net

