'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 22.08.2024

@author: jringelstein
'''

import pandas as pd
import networkx as nx
import uuid
from pandaict.utils.utils import uuid2elt, get_elts_any, to_elt, get_values_for_links
from pandaict.topology.routing_utils import create_multidigraph, __get_nx_node_for_elt, __get_possible_routes, __get_end_nxnodes_for_conn, __print_paths
from pandaict.topology.lup_table import LUP_table
from pandaict.utils.enums import RoutingType, SortType


class IP_table: 
            
    def __init__(self, ict_net, node_elt):
        pass
    
    def view(self):
        pass