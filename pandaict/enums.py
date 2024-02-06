'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from enum import Enum

# Definitions for info items
class InfoItems:
    
    class Measurements(Enum):            
        ACTIVE_POWER         = 1
        CURRENT              = 2
        CURRENT_ANGLE        = 3
        ELECTRIC_METER_VALUE = 4
        FAULT_CODE           = 5
        LOADING_PERCENT      = 6
        REACTIVE_POWER       = 7        
        STATUS               = 8
        SWITCH_POSITION      = 9        
        TAP_POSITION         = 10
        VOLTAGE              = 11  
        VOLTAGE_ANGLE        = 12
    
    class Setpoints(Enum):
        
        ACTIVE_POWER     = 1
        REACTIVE_POWER   = 2                
        SWITCH_POSITION  = 3        
        TAP_POSITION     = 4
        VOLTAGE          = 5
        
        

# Definitions for info items
class NodeType(Enum):        
    SWITCH = 1
    ROUTER = 2
    BRIDGE = 3
