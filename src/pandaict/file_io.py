'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 27.02.2024

@author: jringelstein
'''

import pandas as pd
import os
import json
from packaging.version import Version
import pandapower.io_utils as io_utils
from pandaict.create import create_empty_network
from pandaict.std_types import basic_std_types


def to_json(ict_net, filename=None, encryption_key=None, store_index_names=False):
    """
        Saves a pandaict Network in JSON format. The index columns of all pandas DataFrames will
        be saved in ascending order. net elements which name begins with "_" (internal elements)
        will not be saved. Std types will also not be saved.

        INPUT:
            **ict_net** (dict) - The pandaict format network

            **filename** (string or file, None) - The absolute or relative path to the output file
            or a file-like object, if 'None' the function returns a json string

            **encrytion_key** (string, None) - If given, the pandaict network is stored as an
            encrypted json string

            **store_index_names** (bool, False) - If True, an additional dict "index_names" is
            stored into the json string which includes the index names of the dataframes within the
            net.
            Since pandaict does usually not use net[elm].index.name, the default is False.


        EXAMPLE:

             >>> pp.to_json(net, "example.json")

    """
    # --- store index names
    if store_index_names:
        # To ensure correct index names (see https://github.com/e2nIEE/pandapower/issues/1410),
        # these are additionally stored to the json file as a dict.
        if "index_names" in ict_net.keys():
            raise ValueError("To store DataFrame index names, 'index_names' "
                             "is used and thus should not be a key of net.")
        ict_net["index_names"] = {
            key: ict_net[key].index.name for key in ict_net.keys() if isinstance(
                ict_net[key], pd.DataFrame) and isinstance(ict_net[key].index.name, str) and \
                ict_net[key].index.name != ""
        }

    json_string = json.dumps(ict_net, cls=io_utils.PPJSONEncoder, indent=2)
    if encryption_key is not None:
        json_string = io_utils.encrypt_string(json_string, encryption_key)

    if store_index_names:
        # remove the key "index_names" to not change net
        del ict_net["index_names"]

    if filename is None:
        return json_string

    if hasattr(filename, 'write'):
        filename.write(json_string)
    else:
        with open(filename, "w") as fp:
            fp.write(json_string)



def from_json(filename, encryption_key=None, elements_to_deserialize=None,
              keep_serialized_elements=True, add_basic_std_types=False, replace_elements=None):
    """
    Load a pandaict network from a JSON file.
    The index of the returned network is not necessarily in the same order as the original network.
    Index columns of all pandas DataFrames are sorted in ascending order.

    INPUT:
        **filename** (string or file) - The absolute or relative path to the input file or
        file-like object    

        **encrytion_key** (string, "") - If given, key to decrypt an encrypted pandaict network

        **elements_to_deserialize** (list, None) - Deserialize only certain pandaict elements.
        If None all elements are deserialized.

        **keep_serialized_elements** (bool, True) - Keep serialized elements if given.
        Default: Serialized elements are kept.

        **add_basic_std_types** (bool, False) - Add missing standard-types from pandaict standard
        type library.

        **replace_elements** (dict, None) - Keys are replaced by values found in json string.
        Both key and value are supposed to be strings.    

    OUTPUT:
        **ict_net** (dict) - The pandaict format network

    EXAMPLE:

        >>> net = pp.from_json("example.json")

    """
    if hasattr(filename, 'read'):
        json_string = filename.read()
    elif not os.path.isfile(filename):
        raise UserWarning("File {} does not exist!!".format(filename))
    else:
        with open(filename, "r") as fp:
            json_string = fp.read()

    return from_json_string(
        json_string,        
        encryption_key=encryption_key,
        elements_to_deserialize=elements_to_deserialize,
        keep_serialized_elements=keep_serialized_elements,
        add_basic_std_types=add_basic_std_types,
        replace_elements=replace_elements)


def from_json_string(json_string, encryption_key=None, elements_to_deserialize=None,
                     keep_serialized_elements=True, add_basic_std_types=False,
                     replace_elements=None):
    """
    Load a pandaict network from a JSON string.
    The index of the returned network is not necessarily in the same order as the original network.
    Index columns of all pandas DataFrames are sorted in ascending order.

    INPUT:
        **json_string** (string) - The json string representation of the network

        **encrytion_key** (string, "") - If given, key to decrypt an encrypted json_string

        **elements_to_deserialize** (list, None) - Deserialize only certain pandaict elements.
            If None all elements are deserialized.

        **keep_serialized_elements** (bool, True) - Keep serialized elements if given.
            Default: Serialized elements are kept.

        **add_basic_std_types** (bool, False) - Add missing standard-types from pandaict standard
        type library.

        **replace_elements** (dict, None) - Keys are replaced by values found in json string.
        Both key and value are supposed to be strings.    

    OUTPUT:
        **ict_net** (dict) - The pandaict format network

    EXAMPLE:

        >>> net = pp.from_json_string(json_str)

    """
    if replace_elements is not None:
        for k, v in replace_elements.items():
            json_string = json_string.replace(k, v)

    if encryption_key is not None:
        json_string = io_utils.decrypt_string(json_string, encryption_key)

    if elements_to_deserialize is None:
        ict_net = json.loads(json_string, cls=io_utils.PPJSONDecoder,
                         empty_dict_like_object=None)
    else:
    
        ict_net = json.loads(json_string, cls=io_utils.PPJSONDecoder, deserialize_pandas=False,
                         empty_dict_like_object=None)
        net_dummy = create_empty_network()
        
        if keep_serialized_elements:
            for key in elements_to_deserialize:
                ict_net[key] = json.loads(ict_net[key], cls=io_utils.PPJSONDecoder)
        else:        
            for key in ict_net.keys():
                if key in elements_to_deserialize:
                    ict_net[key] = json.loads(ict_net[key], cls=io_utils.PPJSONDecoder)
                elif not isinstance(ict_net):
                    continue
                elif 'pandas' in ict_net[key]:
                    ict_net[key] = net_dummy[key]
    
            # compare pandapowerNet-format_version and package-version
            io_utils.check_net_version(ict_net)
        
    if add_basic_std_types:
        # get std-types and add only new keys ones
        for key, std_types in basic_std_types().items():
            ict_net.std_types[key] = dict(std_types, **ict_net.std_types[key])

    return ict_net
    