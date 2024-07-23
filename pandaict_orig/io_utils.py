import pandaict_orig as pi

import pandas as pd
import os
import json
from numpy import int64
import csv
from pandapower.io_utils import PPJSONEncoder, PPJSONDecoder
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
    json_string = to_json_string(ict_net)
    if hasattr(filename, 'write'):
        filename.write(json_string)
        return
    with open(filename, "w") as text_file:
        text_file.write(json_string)


def to_json_string(ict_net):
    """
        Returns a pandaict Network in JSON format. The index columns of all pandas DataFrames will
        be saved in ascending order. net elements which name begins with "_" (internal elements)
        will not be saved. Std types will also not be saved.

        INPUT:
            **ict_net** (dict) - The pandaict format network

            **filename** (string) - The absolute or relative path to the input file.

        EXAMPLE:

             >>> json = pi.to_json_string(ict_net)

    """
    json_string = "{"
    for k in sorted(ict_net.keys()):
        if k[0] == "_":
            continue
        json_string += '"%s":%s,' % (k, json.dumps(ict_net[k], cls=PPJSONEncoder, indent=4))
    json_string = json_string[:-1] + "}\n"
    return json_string


def from_json(filename, convert=True):
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
    if hasattr(filename, 'read'):
        data = json.load(filename, cls=PPJSONDecoder)
    elif not os.path.isfile(filename):
        raise UserWarning("File %s does not exist!!" % filename)
    else:
        with open(filename) as data_file:
            data = json.load(data_file, cls=PPJSONDecoder)
    try:
        pd_dicts = dicts_to_pandas(data)
        ict_net = from_dict_of_dfs(pd_dicts)
#        if convert:
#            convert_format(net)
        return ict_net
    except UserWarning:
        # Can be deleted in the future, maybe now
        return from_json_dict(data, convert=convert)













def dicts_to_pandas(json_dict):
    pd_dict = dict()
    for k in sorted(json_dict.keys()):
        if isinstance(json_dict[k], dict):
            pd_dict[k] = pd.DataFrame.from_dict(json_dict[k], orient="columns")
            if pd_dict[k].shape[0] == 0:  # skip empty dataframes
                continue
            if pd_dict[k].index[0].isdigit():
                pd_dict[k].set_index(pd_dict[k].index.astype(numpy.int64), inplace=True)
        else:
            raise UserWarning("The network is an old version or corrupt. "
                              "Try to use the old load function")
    return pd_dict


def from_json_dict(json_dict, convert=True):
    """
    Load a pandapower network from a JSON string.
    The index of the returned network is not necessarily in the same order as the original network.
    Index columns of all pandas DataFrames are sorted in ascending order.

    INPUT:
        **json_dict** (json) - The json object representation of the network

    OUTPUT:
        **convert** (bool) - use the convert format function to

        **net** (dict) - The pandapower format network

    EXAMPLE:

        >>> net = pp.pp.from_json_dict(json.loads(json_str))

    """
    ict_net = pi.create_empty_ict_network()

    # checks if field exists in empty network and if yes, matches data type
    def check_equal_type(name):
        if name in ict_net:
            if isinstance(ict_net[name], type(json_dict[name])):
                return True
            elif isinstance(ict_net[name], pd.DataFrame) and isinstance(json_dict[name], dict):
                return True
            elif GEOPANDAS_INSTALLED and \
                    isinstance(ict_net[name], pd.DataFrame) and \
                    isinstance(json_dict[name], GeoDataFrame):
                return True
            else:
                return False
        return True

    for k in sorted(json_dict.keys()):
        if k == 'dtypes':
            continue
        if not check_equal_type(k):
            raise UserWarning("Different data type for existing pandapower field %s: %s vs. %s (%s)"
                              % (k, type(ict_net[k]), type(json_dict[k]), json_dict[k]))
        if isinstance(json_dict[k], dict) and isinstance(ict_net[k], pd.DataFrame):
                ict_net[k] = pd.DataFrame.from_dict(json_dict[k], orient="columns")
                ict_net[k].set_index(ict_net[k].index.astype(numpy.int64), inplace=True)
        else:
            ict_net[k] = json_dict[k]
#    if convert:
#        convert_format(net)
    return ict_net
