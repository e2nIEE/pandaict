'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 10.09.2024

@author: jringelstein
'''

from pandaict.utils.utils import get_elts_any
from pandaict.pilogger import pilogger

def __get_next_hop(ict_net, l, lni):
    if l['from'][0]=="device" or l['from']==lni:            
        nni = l['to'] # next node  
        if isinstance(nni, list):
            nni = nni[0]           
    else:            
        nni = l['from']            
    nn = get_elts_any(ict_net, nni)
    return nn, nni 

def __check_calc_route(ict_net, links, caller_string): # caller_strring: calc_ber_route, calc_MTBF_MTTR_route
    if not isinstance(links, list): 
        pilogger.warn(caller_string+" links parameter must be list")
        return False
    for li in links:
        l = get_elts_any(ict_net, li)
        if isinstance(l['to'], list) and len(l['to'])>1: 
            pilogger.warn(caller_string+" currently doesn't support routes with multicast")
            return False
    lf = get_elts_any(ict_net, links[0]) # first link
    ll = get_elts_any(ict_net, links[-1]) # last link
    if not (lf['from'][0]=="device" or lf['to'][0][0]=="device") or not (ll['from'][0]=="device" or ll['to'][0][0]=="device"):
        pilogger.warn(caller_string+" first and last link must be connected to devices")
        return False
    return True 

def __check_lup_prob_sum_lt_one(lup_table, downstream):
    pr_sum = 0    
    for r in lup_table:
        if r['downstream']!=downstream:
            continue
        pr_sum += r['probability']
    if pr_sum > 1.0:
        pilogger.warn("calc_MTBF_MTTR_by_lup: lup table probabilities add up to "+str(pr_sum)+", maximal supported: 1.0")
        return False 
    return True 
    

