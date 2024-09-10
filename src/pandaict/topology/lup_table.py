'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 30.01.2024

@author: jringelstein
'''

from pandaict.utils.utils import uuid2elt, get_elts_any

class LUP_table: 
            
    def __init__(self, ict_net, conn_elt):
        
        # prepare datastructure for lup table
        # DataFrames are terrible. Just use a list of dict for now.         
        self._lupdf = [] 
        
        # set connection element and connection
        self.conn_elt = conn_elt      
        self.conn = get_elts_any(ict_net, conn_elt, expected=['conn'])
        
        self._index = 0
        self._num_routes = 0
        
    def __iter__(self):
        return self

    def __next__(self):
        if self._index < self._num_routes:
            item = self.get_route(self._index)
            self._index += 1
            return item
        else:
            self._index = 0
            raise StopIteration
        
    def add_route(self, downstream: bool, delivering: bool, probability: float, links: list, hops: list):        
        new_entry = {'downstream': downstream, 'delivering': delivering, 'probability': probability, 'links': links}
        if hops is not None: 
            new_entry.update({'hops': hops})
        self._lupdf += [new_entry]
        self._num_routes += 1
    
    def get_route(self, idx):
        if idx >= len(self._lupdf):
            return None
        else:
            return self._lupdf[idx]
    
    