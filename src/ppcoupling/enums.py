'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from enum import Enum

# Definitions for info items
class ppMeasurements(Enum):            
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

class ppSetpoints(Enum):
    
    ACTIVE_POWER     = 1
    REACTIVE_POWER   = 2                
    SWITCH_POSITION  = 3        
    TAP_POSITION     = 4
    VOLTAGE          = 5
          
class ppDeviceType(Enum):        
    MEASUREMENT    = 1 # Pure Measurement device (multiple values can be measured) 
    ACTUATOR       = 2 # Pure Actuation device with no local control capability (German: "Steuerung")  
    CONTROLLER     = 3 # Combination of Actuator and Measurement type, may perform closed-loop control 
    CONTROLCENTER  = 4 # Receives/processes measurements, sends setpoints, but doesn't control an appliance
