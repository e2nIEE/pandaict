'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from aenum import Enum, extend_enum
import pandas as pd

# Definitions for info items
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
    
class NodeType(Enum):        
    SWITCH    = 1
    ROUTER    = 2

class DeviceType(Enum):        
    CONVERTER      = 1 # Hosts Converter type app
    SERVER         = 2
    RTU            = 3
    
class AppType(Enum):  
    CONVERTER      = 1 # Converts between different protocolss          
    WEBSERVER      = 3
    FILESERVER     = 4 
    CLIENT         = 5
    RESTSERVER     = 6
    RESTCLIENT     = 7
    
class RoutingType(Enum):  
    # RANDOM_ROUNDROBIN       = 1                            
    # FLOODING                = 2
    LOWEST_TOTAL_LATENCY      = 3 
    # BALANCED_BANDWITH_USAGE = 4
    
class SortType(Enum):  
    USAGE           = 1
    LATENCY         = 2
    BIT_ERROR_RATE  = 3 
    BANDWIDTH       = 4
    
    
def addCustomEnum(net, etype, name, value=None):    
    if name not in [m.name for m in etype.__members__.values()]:  # if enum doesn't exist           
        if value is None:
            maxvalue = max([m.value for m in etype.__members__.values()])
            value = 1000 if maxvalue<1000 else maxvalue+1        
        extend_enum(etype, name, value)
    else:
        value = etype[name].value # if anready existing, still add it to net custom enums    
    if "custom_enums" not in net.keys():
        net.custom_enums = pd.DataFrame(columns=['name', 'type', 'value']) 
    # Check if new enum exists in net
    for _, ce in net.custom_enums.iterrows():
        if ce['name']==name and ce['type']==etype:
            return 
    net.custom_enums.loc[len(net.custom_enums)] = [name, etype, value]
    
