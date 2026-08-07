'''
Created on 30.01.2024
@author: jringelstein <jan.ringelstein@iee.fraunhofer.de>

SPDX-FileCopyrightText: Copyright (c) 2024-2026 by Fraunhofer IEE, Kassel. All rights reserved.
SPDX-License-Identifier: BSD-3-Clause

'''

from aenum import Enum, extend_enum
import pandas as pd

# Definitions for info items
# NOTE: Values of 1000 or larger are reserved for custom enums
class InfoItem(Enum):
    ACK         = 1
    VALUE       = 2
    REQUEST     = 3
    RESPONSE    = 4
    STATUS      = 5
    URL         = 6
    FILE        = 7
    TEXT        = 8
    WEBPAGE     = 9
    TIME        = 10
    CERTIFICATE = 11
    AUDIOSTREAM = 12
    VIDEOSTREAM = 13    
    
# NOTE: Values of 1000 or larger are reserved for custom enums
class NodeType(Enum):        
    SWITCH    = 1
    ROUTER    = 2

# NOTE: Values of 1000 or larger are reserved for custom enums
class DeviceType(Enum):        
    CONVERTER      = 1 # Hosts Converter type app
    SERVER         = 2
    RTU            = 3
    
# NOTE: Values of 1000 or larger are reserved for custom enums
class AppType(Enum):  
    CONVERTER      = 1 # Converts between different protocolss          
    WEBSERVER      = 3
    FILESERVER     = 4 
    CLIENT         = 5
    RESTSERVER     = 6
    RESTCLIENT     = 7
    
class RoutingType(Enum):  
    LOWEST_TOTAL_LATENCY      = 3
    
class SortType(Enum):  
    USAGE           = 1
    LATENCY         = 2
    BIT_ERROR_RATE  = 3 
    BANDWIDTH       = 4
    
def add_custom_enum(net, etype, name, value=None):    
    """
    Adds a custom enum to net at runtime. Enums defined herewith are assigned values of 1000 or higher by default. They are added to a 
    **net.custom_enums** dataframe to track and tag them as custom. They are saved to JSON and Excel files. 
    
    If a custom enum is added with the same name as an existing one, the existing will be retained and not be assigned a new value.

    :INPUT:
        **net** (pandaictNet) - The pandaict network to which the enum is added. 
        
        **etype** (aenum) - One of the predefined enum types, i.e. NodeType, DeviceType, AppType, InfoItem, RoutingType, and SortType    
        
        **name** (string, default None) - the name for the new enum

    :OPTIONAL:
        **value** (int, default None) - fixed value for this enum. Note: if an already existing value is used, the custom enum 
        is *not* created. 

    :EXAMPLE:
        add_custom_enum(net, NodeType, "REPEATER")
    """
    
    if name not in [m.name for m in etype.__members__.values()]:  # if enum doesn't exist           
        if value is None:
            maxvalue = max([m.value for m in etype.__members__.values()])
            value = 1000 if maxvalue<1000 else maxvalue+1        
        extend_enum(etype, name, value)
    else:
        value = etype[name].value # if already existing, still add it to net custom enums
    if "custom_enums" not in net.keys():
        net.custom_enums = pd.DataFrame(columns=['name', 'type', 'value']) 
    # Check if new enum exists in net
    for _, ce in net.custom_enums.iterrows():
        if ce['name']==name and ce['type']==etype:
            return 
    net.custom_enums.loc[len(net.custom_enums)] = [name, etype, value]
    