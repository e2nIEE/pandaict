'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from pandapower.auxiliary import ADict, get_free_id, _preserve_dtypes
import pandaict as pi
import pandas as pd
import copy
import numpy as np

class pandaICTNet(ADict):
    def __init__(self, *args, **kwargs):        
        super(pandaICTNet, self).__init__(*args, **kwargs)
                
    def deepcopy(self):
        return copy.deepcopy(self)

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

def plural_s(number):
    if number > 1:
        return "s"
    else:
        return ""