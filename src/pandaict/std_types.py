'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 2.02.2024

@author: jringelstein
'''

import pandas as pd
import warnings
from   pandaict.enums import Measurements as Meas
from   pandaict.enums import Setpoints as Setp
from   pandaict.enums import NodeType

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


def basic_link_std_types():

    linktypes = {        
        "Binary":
            { "bandwidth_Mbps": (0.001),
              "latency_ms": 1,
              "wired": True,
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
            },
        "RS485":
            { "bandwidth_Mbps": (0.1),
              "latency_ms": 100,
              "wired": True,
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
            },
        "LTE50": # LTE with downstream bandwidth of 50 Mbps
            { "bandwidth_Mbps": (50,10),
              "latency_ms": 300,
              "wired": False,
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
            },
        "LAN1000": # Gigabit LAN
            { "bandwidth_Mbps": (1000, 1000),
              "latency_ms": 100,
              "wired": True,
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
            },
        "ADSL8": # Asymmetric DSL with downstream bandwidth of 8 Mbps
            { "bandwidth_Mbps": (8, 1),
              "latency_ms": 100,
              "wired": True,
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
            },
        "Fiber": # Glass fiber
            { "bandwidth_Mbps": (1000, 1000),
              "latency_ms": 100,
              "wired": True,
              "ber_per_km": 0,
              "mtbf_h": 0,
              "mttr_h": 0,
            }
        }
    
    
    return linktypes

def basic_protocol_std_types():

    protocoltypes = { 
        "IEC104-TCP": {        
            "base_package_size_byte": 1024,
            "info_items":
                [ Meas.ACTIVE_POWER,
                 Meas.CURRENT,
                 Meas.CURRENT_ANGLE,
                 Meas.FAULT_CODE,
                 Meas.LOADING_PERCENT,
                 Meas.LOADING_PERCENT,
                 Meas.REACTIVE_POWER,
                 Meas.STATUS,
                 Meas.SWITCH_POSITION,
                 Meas.TAP_POSITION,
                 Meas.VOLTAGE,
                 Meas.VOLTAGE_ANGLE,
                 Setp.ACTIVE_POWER,
                 Setp.REACTIVE_POWER,
                 Setp.SWITCH_POSITION,
                 Setp.TAP_POSITION,
                 Setp.VOLTAGE,
                ],    
            },
        "MODBUS-TCP": {        
            "base_package_size_byte": 1024,
            "info_items":
                [ Meas.ACTIVE_POWER,
                 Meas.CURRENT,
                 Meas.CURRENT_ANGLE,
                 Meas.FAULT_CODE,                 
                 Meas.REACTIVE_POWER,
                 Meas.STATUS,
                 Meas.SWITCH_POSITION,                 
                 Setp.ACTIVE_POWER,
                 Setp.REACTIVE_POWER,
                 Setp.SWITCH_POSITION,           
                ],    
            },
        "IEC61850_MMC": {
            "name": "IEC61850-MMC",
            "base_package_size_byte": 1024,
            "info_items":
                [ Meas.ACTIVE_POWER,
                 Meas.CURRENT,
                 Meas.CURRENT_ANGLE,
                 Meas.FAULT_CODE,
                 Meas.LOADING_PERCENT,
                 Meas.LOADING_PERCENT,
                 Meas.REACTIVE_POWER,
                 Meas.STATUS,
                 Meas.SWITCH_POSITION,
                 Meas.TAP_POSITION,
                 Meas.VOLTAGE,
                 Meas.VOLTAGE_ANGLE,
                 Setp.ACTIVE_POWER,
                 Setp.REACTIVE_POWER,
                 Setp.SWITCH_POSITION,
                 Setp.TAP_POSITION,
                 Setp.VOLTAGE,
                ],
            },
        "Binary": {        
            "base_package_size_byte": 1,
            "info_items":
                [ Meas.SWITCH_POSITION,
                 Meas.STATUS,
                  Setp.SWITCH_POSITION,           
                ],    
            },
        }
    
    return protocoltypes



def basic_std_types():
    return {
        "link"       : basic_link_std_types(), 
        "protocol"   : basic_protocol_std_types(),           
    }
    
def add_basic_std_types(ict_net):
    """Adds basic standard types of the pandaict library to the ict_net provided. These standard types
    are the same types that are available with output of `pandapower.create_empty_network()` and
    `pandapower.create_empty_network(add_stdtypes=True)` respectively.

    Parameters
    ----------
    ict_net : pandapowerNet
        pandaict net which should receive the basic standard types

    Returns
    -------
    tuple of dictionaries
        standard types as dictionaries which have been added to the ict_net.
    """

    if "std_types" not in ict_net:
        ict_net.std_types = {"link": {}}
        ict_net.std_types.update({"protocol": {}})

    linktypes = basic_link_std_types()
    protocols = basic_protocol_std_types()

    create_std_types(ict_net, data=linktypes, element="link")
    create_std_types(ict_net, data=protocols, element="protocol")  
        
    return linktypes    