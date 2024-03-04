'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from enum import Enum

# Definitions for info items
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
    SWITCH    = 1
    ROUTER    = 2

class DeviceType(Enum):        
    CONVERTER      = 1 # Converts between different protocols
    MEASUREMENT    = 2 # Pure Measurement device (multiple values can be measured) 
    ACTUATOR       = 3 # Pure Actuation device with no local control capability (German: "Steuerung")  
    CONTROLLER     = 4 # Combination of Actuator and Measurement type, may perform closed-loop control 
    CONTROLCENTER  = 5 # Receives/processes measurements, sends setpoints, but doesn't control an appliance
