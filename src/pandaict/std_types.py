'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 2.02.2024

@author: jringelstein
'''

import pandas as pd
import warnings
import uuid
from   pandaict.utils.enums import InfoItem

try:
    import pandaplan.core.pplog as logging
except ImportError:
    import logging

logger = logging.getLogger(__name__)


def create_std_type(ict_net, data, name, element="link", overwrite=True, check_required=True):
    """
    Creates type data in the type dict. The following mandatory parameters have to be at least contained in data:
    
        - bandwidth_Mbps, latency_ms, wired (for links)
        - info_items (for protocols)
        
    additional parameters can be added and later loaded into pandaict with the function
    "parameter_from_std_type".

    The standard type is saved into the pandaict dict of the given network by default.

    INPUT:
        **ict_net** - The pandaict network
        **data** - dictionary of standard type parameters
        **name** - name of the standard type as string
        **element** - "link"
    
    """

    if data is None: 
        return 
    
    if type(data) != dict:
        raise UserWarning("type data has to be given as a dictionary of parameters")

    if check_required:
        if element == "link":
            required = ["bandwidth_Mbps", "latency_ms", "wired"]
        elif element == "protocol":
            required = ["info_items"]
        else:
            raise ValueError("Unkown element type %s" % element)
        for par in required:
            if par not in data:
                raise UserWarning("%s is required as %s type parameter" % (par, element))
    stdict = ict_net.std_types[element]
    if overwrite or not (name in stdict):
        stdict.update({name: data})


def create_std_types(ict_net, data, element="link", overwrite=True, check_required=True):
    """
    Creates multiple standard types in the type dict.

    INPUT:
        **ict_net** - The pandaict network
        **data**    - dictionary of standard type parameter sets
        **element** - "link"

    """
    for name, typdata in data.items():
        create_std_type(ict_net, data=typdata, name=name, element=element, overwrite=overwrite,
                        check_required=check_required)


def __basic_link_std_types():

    linktypes = {        
        "Binary":
            { "bandwidth_Mbps": (0.001),
              "latency_ms": 1,
              "wired": True,
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
              "uuid": uuid.UUID("0a004f60-1df4-449c-94b5-08809ad686d1"),
            },
        "RS485":
            { "bandwidth_Mbps": (0.1),
              "latency_ms": 100,
              "wired": True,        
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
              "uuid": uuid.UUID("77fbef84-195f-40de-882b-3d8824c0d3a5"),
            },
        "LTE50": # LTE with downstream bandwidth of 50 Mbps
            { "bandwidth_Mbps": (50,10),
              "latency_ms": 300,
              "wired": False,
              "protocols": ['FTP','HTTP'],
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
              "uuid": uuid.UUID("cd43d4c0-66d2-4723-886a-7c937e259c5a"),
            },
        "LAN1000": # Gigabit LAN
            { "bandwidth_Mbps": (1000, 1000),
              "latency_ms": 100,
              "wired": True,
              "protocols": ['FTP','HTTP'],
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
              "uuid": uuid.UUID("4d5b388f-ce1c-407e-81c6-5caa23f1832b"),
            },
        "ADSL8": # Asymmetric DSL with downstream bandwidth of 8 Mbps
            { "bandwidth_Mbps": (8, 1),
              "latency_ms": 100,
              "wired": True,
              "protocols": ['FTP','HTTP'],
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
              "uuid": uuid.UUID("6dd01923-0bce-4f07-8ef0-65a0f214d2cf"),
            },
        "Fiber": # Glass fiber
            { "bandwidth_Mbps": (1000, 1000),
              "latency_ms": 100,
              "wired": True,
              "protocols": ['FTP','HTTP'],
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
              "uuid": uuid.UUID("eebc167b-b816-468f-bb9a-5e75c7ccd79b"),
            }
        }    
    
    return linktypes

def __basic_protocol_std_types():

    protocoltypes = {
        "FTP": {        
            "base_package_size_byte": 4096,
            "info_items":
                [ InfoItem.REQUEST,
                  InfoItem.RESPONSE, 
                  InfoItem.TEXT,
                  InfoItem.FILE, 
                  InfoItem.STATUS,
                ], 
            "uuid": uuid.UUID("30e8be5c-06d8-4914-b99b-31f015473599"),   
            },
        "HTTP": {        
            "base_package_size_byte": 4096,
            "info_items":
                [ InfoItem.REQUEST,
                  InfoItem.RESPONSE, 
                  InfoItem.WEBPAGE, 
                  InfoItem.STATUS,                 
                ],    
            "uuid": uuid.UUID("9bd957a0-1e02-4925-bef6-8cf04c5e9ead"),
            },
        }        
    
    return protocoltypes



def __basic_std_types():
    return {
        "link"       : __basic_link_std_types(), 
        "protocol"   : __basic_protocol_std_types(),           
    }
    
def add_basic_std_types(ict_net): # ToDo: make private?
    """Adds basic standard types of the pandaict library to the ict_net provided. These standard types
    are the same types that are available with output of `pandapower.create_empty_network()` and
    `pandapower.create_empty_network(add_stdtypes=True)` respectively.

    Parameters
    ----------
    ict_net : pandaICT
        pandaICT net which should receive the basic standard types

    Returns
    -------
    tuple of dictionaries
        standard types as dictionaries which have been added to the ict_net.
    """

    if "std_types" not in ict_net:
        ict_net.std_types = {"link": {}}
        ict_net.std_types.update({"protocol": {}})

    linktypes = __basic_link_std_types()
    protocols = __basic_protocol_std_types()

    create_std_types(ict_net, data=linktypes, element="link")
    create_std_types(ict_net, data=protocols, element="protocol")  
        
    return linktypes    