'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from enum import Enum

# Definitions for info items
class InfoItems(Enum):
    ACK         = 1
    REQUEST     = 2
    RESPONSE    = 3
    STATUS      = 4
    URL         = 5
    FILE        = 6
    TEXT        = 7
    WEBPAGE     = 8
    TIME        = 9
    CERTIFICATE = 10
    AUDIOSTREAM = 11
    VIDEOSTREAM = 12
    
class NodeType(Enum):        
    SWITCH    = 1
    ROUTER    = 2

class DeviceType(Enum):        
    CONVERTER      = 1 # Converts between different protocols
    SERVER         = 2
    WEBSERVER      = 3
    FILESERVER     = 4 
    CLIENT         = 5
