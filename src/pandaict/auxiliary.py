'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from pandapower.auxiliary import ADict, get_free_id, _preserve_dtypes
#import pandaict as pi
import pandas as pd
import copy
import numpy as np


import json
from pandapower.io_utils import FromSerializableRegistry 
from functools import singledispatch


class pandaICTNet(ADict):
    """
    Example documentation for classes in pandaICTNet
    """
      
    def __init__(self, *args, **kwargs):        
        """
        Initializes a new instance of pandaICTNet

        Parameters
        ----------
        :param args: Example argument
        """
        super(pandaICTNet, self).__init__(*args, **kwargs)
        for key in self:
            if isinstance(self[key], list):
                self[key] = pd.DataFrame(np.zeros(0, dtype=self[key]), index=pd.Index([],
                                         dtype=np.int64))
                
    def deepcopy(self):
        return copy.deepcopy(self)
    
    @FromSerializableRegistry.from_serializable.register(class_name='pandaICTNet', module_name='pandaICTNet.pandaICTNet')    
    def pandaICTNet(self):
        if isinstance(self.obj, str):  # backwards compatibility
            from pandapower import from_json_string
            return from_json_string(self.obj)
        else:            
            net = create_empty_network()            
            net.update(self.obj)
            return net
        
    def __repr__(self):  # pragma: no cover
        """
        See Also
        --------
        count_elements
        """
        par = []
        res = []
        for et in list(self.keys()):
            if not et.startswith("_") and isinstance(self[et], pd.DataFrame) and len(self[et]) > 0:
                n_rows = self[et].shape[0]
                if 'res_' in et:
                    res.append("   - %s (%i %s)" % (et, n_rows, "element" + plural_s(n_rows)))
                elif et == 'group':
                    n_groups = len(set(self[et].index))
                    par.append('   - %s (%i %s, %i %s)' % (
                        et, n_groups, "group" + plural_s(n_groups), n_rows, "row" + plural_s(n_rows)))
                else:
                    par.append("   - %s (%i %s)" % (et, n_rows, "element" + plural_s(n_rows)))
        res_cost = [" and the following result values:",
                    "   - %s" % "res_cost"] if "res_cost" in self.keys() else []
        if not len(par) + len(res):
            return "This pandapower network is empty"
        if len(res):
            res = [" and the following results tables:"] + res
        lines = ["This pandapower network includes the following parameter tables:"] + \
            par + res + res_cost
        return "\n".join(lines)
    
    def equals_excluding_uuids_and_std_types(self, other):
        keys = list(self.keys())
        if 'name' in keys:
            keys.remove('name')
        if 'std_types' in keys: 
            keys.remove('std_types')
        for k in keys:
            cols = list(self[k].columns)
            if 'uuid' in cols: 
                cols.remove('uuid')            
            if not (self[k][cols].compare(other[k][cols]).empty):
                return False 
        return True

def plural_s(number):
    if number > 1:
        return "s"
    else:
        return ""