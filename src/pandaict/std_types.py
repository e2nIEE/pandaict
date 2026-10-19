'''
Created on 2.02.2024
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
'''

import uuid
from pandaict.utils.enums import InfoItem
from pandaict.pilogger import pilogger


def create_std_type(ict_net, data, name, element="link", overwrite=True, custom=True, check_required=True):
    """
    Creates type data in the type dict. The following mandatory parameters have to be at least contained in data:
    
        - bandwidth_Mbps, latency_ms, wired (for links)
        - info_items (for protocols)
        
    The standard type is saved into the pandaict dict of the given network by default.

    :INPUT:
    
        **ict_net** (pandaictNet) - The pandaict network
    
        **data** (dict) - dictionary of standard type parameters (without the name)
    
        **name** (string) - name of the standard type as string
                            NOTE: if a standard type with this already exists, it is overwritten.
    
        **element** (string, default "link" - Element type, may be "link" or "protocol"
    
        **overwrite** (boolean, default True) - If True, overwrites existing std type with same name. If False, only inserts new type when name is not used yet.
    
        **check_required** (boolean, default True) - If True, function fails if required parameters are not present. If False, no checks are made. 
    
    """

    if data is None: 
        return 
    
    if not isinstance(data, dict):
        raise UserWarning("type data has to be given as a dictionary of parameters")

    if check_required:
        if element == "link":
            required = ["bandwidth_Mbps", "latency_ms", "wired"]
        elif element == "protocol":
            required = ["base_package_size_byte", "info_items"]
        else:
            raise ValueError("Unkown element type %s" % element)
        for par in required:
            if par not in data:
                raise UserWarning("%s is required as %s type parameter" % (par, element))
    stdict = ict_net.std_types[element]
    if overwrite or name not in stdict:
        if custom:
            data.update({'custom': True})
        stdict.update({name: data})


def create_std_types(ict_net, data, element="link", overwrite=True, custom=True, check_required=True):
    """
    Creates multiple standard types in the type dict.

    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network
       
        **data** (dict) - dictionary of standard type parameters (including type names)
                          NOTE: if a standard type with given name already exists, it is overwritten.
       
        **element** (string, default "link" - Element type, may be "link" or "protocol"
       
        **overwrite** (boolean, default True) - If True, overwrites existing std type with same name(s). If False, only inserts new type when name is not used yet.
       
        **check_required** (boolean, default True) - If True, function fails if required parameters are not present. If False, no checks are made. 

    """
    for name, typdata in data.items():
        create_std_type(ict_net, data=typdata, name=name, element=element, overwrite=overwrite,
                        custom=custom, check_required=check_required)


def __controller_area_linktypes():
    lt = {"Binary":
            { "bandwidth_Mbps": (0.001),
              "latency_ms": 1,
              "wired": True,
              "protocols": ['Binary'],
              "ber_per_km": 0.00001,
              "mtbf_h": 6000,
              "mttr_h": 0.5,
              "uuid": uuid.UUID("0a004f60-1df4-449c-94b5-08809ad686d1"),
            },
        "RS485":
            { "bandwidth_Mbps": (0.1),
              "latency_ms": 100,
              "wired": True,    
              "protocols": ['MODBUS-SMA'],    
              "ber_per_km": 0.00001,
              "mtbf_h": 6000,
              "mttr_h": 0.5,
              "uuid": uuid.UUID("77fbef84-195f-40de-882b-3d8824c0d3a5"),
            }
        }
    return lt
    
def __local_area_linktypes():
    lt = { "LAN1000": # Gigabit LAN
            { "bandwidth_Mbps": (1000, 1000),
              "latency_ms": 100,
              "wired": True,
              "protocols": ['TCP','UDP','FTP','HTTP','HTTPS','MODBUS-TCP'],
              "ber_per_km": 0.00000002,
              "mtbf_h": 8000,
              "mttr_h": 2,
              "uuid": uuid.UUID("4d5b388f-ce1c-407e-81c6-5caa23f1832b"),
            }
        }
    return lt 

def __wide_area_linktypes():
    lt = {"LTE50": # LTE with downstream bandwidth of 50 Mbps
            { "bandwidth_Mbps": (50,10),
              "latency_ms": (100,200),
              "wired": False,
              "protocols": ['TCP','UDP','FTP','HTTP','HTTPS','MODBUS-TCP'],
              "ber_per_km": 0.00000001,
              "mtbf_h": 5000,
              "mttr_h": 0.5,
              "uuid": uuid.UUID("cd43d4c0-66d2-4723-886a-7c937e259c5a"),
            },
        "UMTS": 
            { "bandwidth_Mbps": (0.04,0.04),
              "latency_ms": (300,300),
              "wired": False,
              "protocols": ['TCP','UDP','FTP','HTTP','HTTPS','MODBUS-TCP'],
              "ber_per_km": 0.0000001,
              "mtbf_h": 5000,
              "mttr_h": 0.5,
              "uuid": uuid.UUID("ed41d4c0-64d2-452d-586a-7c937e259c5b"),
            },                
        "ADSL8": # Asymmetric DSL with downstream bandwidth of 8 Mbps
            { "bandwidth_Mbps": (8, 1),
              "latency_ms": (200,300),
              "wired": True,
              "protocols": ['TCP','UDP','FTP','HTTP','HTTPS','MODBUS-TCP'],
              "ber_per_km": 0.0005,
              "mtbf_h": 12000,
              "mttr_h": 10,
              "uuid": uuid.UUID("6dd01923-0bce-4f07-8ef0-65a0f214d2cf"),
            },
        "Fiber": # Glass fiber
            { "bandwidth_Mbps": (1000, 1000),
              "latency_ms": 100,
              "wired": True,
              "protocols": ['TCP','UDP','FTP','HTTP','HTTPS','MODBUS-TCP'],
              "ber_per_km": 0.000000001,
              "mtbf_h": 12000,
              "mttr_h": 2,
              "uuid": uuid.UUID("eebc167b-b816-468f-bb9a-5e75c7ccd79b"),
            }
        }
    return lt

def __basic_link_std_types():

    linktypes = __controller_area_linktypes()
    linktypes.update(__local_area_linktypes())
    linktypes.update(__wide_area_linktypes())    
    return linktypes

def __simple_protocoltypes():
    return {"Binary": {        
                "base_package_size_byte": 1,
                "info_items":
                    [ 
                        InfoItem.VALUE,                     
                    ],    
                "uuid": uuid.UUID("7d188465-eeae-4d42-b048-383f0a1bc6e9"),
                }
            }

def __transmission_protocoltypes():
    pt = {"TCP": {        
            "base_package_size_byte": 20,
            "info_items":
                [ InfoItem.REQUEST,
                  InfoItem.RESPONSE,                   
                ], 
            "uuid": uuid.UUID("fdb0612d-3791-437a-b570-139c49c9dea9"),   
            },
        "UDP": {        
            "base_package_size_byte": 12, # UDP Header has at least 12 byte
            "info_items":
                [ InfoItem.REQUEST,
                  InfoItem.RESPONSE,                   
                ],                                
            "uuid": uuid.UUID("1eec8609-e112-4e7c-ae40-037fac9bdf81"),   
            }
        }
    return pt

def __application_protocoltypes():
    pt = {"HTTP": {        
            "base_package_size_byte": 4096,
            "info_items":
                [ InfoItem.REQUEST,
                  InfoItem.RESPONSE, 
                  InfoItem.URL,
                  InfoItem.WEBPAGE, 
                  InfoItem.STATUS,                 
                ],   
            "payload_size_byte": 
                [ 256,
                  10240,
                  512,
                  61439,
                  128
                ], 
            "uuid": uuid.UUID("9bd957a0-1e02-4925-bef6-8cf04c5e9ead"),
            },
        "HTTPS": {        
            "base_package_size_byte": 4096,
            "info_items":
                [ InfoItem.REQUEST,
                  InfoItem.RESPONSE,
                  InfoItem.URL, 
                  InfoItem.WEBPAGE, 
                  InfoItem.STATUS,                 
                ],    
            "uuid": uuid.UUID("1ab747c1-dd2c-44ca-9915-7f9ae06da7c2"),
            },   
        "FTP": {        
            "base_package_size_byte": 4096,
            "info_items":
                [ InfoItem.REQUEST,
                  InfoItem.RESPONSE,                   
                  InfoItem.TEXT,
                  InfoItem.FILE, 
                  InfoItem.STATUS,
                ], 
            "payload_size_byte": 
                [ 256,
                  256,
                  4096,
                  61493,
                  128
                ], 
            "uuid": uuid.UUID("30e8be5c-06d8-4914-b99b-31f015473599"),   
            }
        }
    return pt  

def __modbus_protocoltypes():
    return {"MODBUS-TCP": {        
                "base_package_size_byte": 1024,
                "info_items":
                    [ InfoItem.REQUEST,
                      InfoItem.RESPONSE,                   
                      InfoItem.STATUS        
                    ],  
                "uuid": uuid.UUID("8adcb11a-e88f-4a36-bf25-a12f720ac728"),  
                },
            "MODBUS-SMA": {        
                "base_package_size_byte": 16,
                "info_items":
                    [ InfoItem.REQUEST,
                      InfoItem.RESPONSE,                   
                      InfoItem.STATUS  
                    ],  
                "uuid": uuid.UUID("41e604ff-a139-452f-a424-6300584ecec3"),  
                }
            }

def __basic_protocol_std_types():

    protocoltypes = __simple_protocoltypes()
    protocoltypes.update(__transmission_protocoltypes())
    protocoltypes.update(__application_protocoltypes())   
    protocoltypes.update(__modbus_protocoltypes())
    return protocoltypes


def __basic_std_types():
    return {
        "link"       : __basic_link_std_types(), 
        "protocol"   : __basic_protocol_std_types(),           
    }
    
def add_basic_std_types(ict_net):
    """Adds basic standard types of the pandaict library to the ict_net provided. These standard types
    are automatically available with output of `create_empty_network()`.

    :INPUT:
        **ict_net** - pandaICT net which should receive the basic standard types

    :OUTPUT:    
        **std_types** (tuple of dict) - standard types as dictionaries which have been added to the ict_net.
    """

    if "std_types" not in ict_net:
        ict_net.std_types = {"link": {}}
        ict_net.std_types.update({"protocol": {}})

    linktypes = __basic_link_std_types()
    protocols = __basic_protocol_std_types()

    create_std_types(ict_net, data=linktypes, element="link", custom=False)
    create_std_types(ict_net, data=protocols, element="protocol", custom=False)  
        
    return linktypes, protocols    