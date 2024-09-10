'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 23.04.2024

@author: jringelstein
'''

from pandaict.utils.enums import InfoItem, NodeType, DeviceType, AppType
from pandaict.utils.utils import get_links_at, get_apps_on_device, get_links_between
from pandaict.pilogger import pilogger

def __log_info_and_return_false(infostring):
    pilogger.info(infostring) 
    return False

def __check_isNone(i, n, elt_type, sparam, passed, checkempty=False):
    if n[sparam] is None or (checkempty and n[sparam]==""):
        passed = __log_info_and_return_false(elt_type+" '" + str(n['name']) + "' (index " + str(i) + ") has no "+sparam)        
    return passed
    
def __inspect_node(ict_net, passed):
    for i, n in ict_net.node.iterrows():
        passed = __check_isNone(i, n, "node", "name", passed)
        passed = __check_isNone(i, n, "node", "type", passed)
        passed = __check_isNone(i, n, "node", "link_types", passed)
        # check if all nodes have two or more links connected
        l = get_links_at(ict_net, ('node', i))
        if len(l) < 2:
            passed = __log_info_and_return_false(" node '" + str(n['name']) + "' (index " + str(i) + ") has less than two links")            
    
    return passed

def __inspect_link(ict_net, passed):
    for i, l in ict_net.link.iterrows():
        passed = __check_isNone(i, l, "link", "name", passed)
        passed = __check_isNone(i, l, "link", "type", passed)
        # from_elt and to_elt existence and non-equality are tested during creation
    
        # check for double linkage (excluding multicasts)
        from_elt = l["from"]
        to_elt   = l["to"][0]
        linklist = get_links_between(ict_net, from_elt, to_elt)
        if len(linklist) > 1: 
            linklist.remove(i)
            passed = __log_info_and_return_false(" link '"+str(l['name'])+"' (index "+str(i)+") has duplicate(s) (indexes "+str(linklist)+")")            
        
    # check std linktypes
    for linktype in ict_net.std_types['link'].keys():
        protocols = ict_net.std_types['link'][linktype]['protocols']
        for p in protocols:
            if p not in ict_net.std_types['protocol'].keys():
                passed = __log_info_and_return_false(" std link type '"+str(linktype)+"' has unknown protocol '"+str(p)+"'")                
    
    return passed


def __inspect_device(ict_net, passed):
    for i, d in ict_net.device.iterrows():
        passed = __check_isNone(i, d, "device", "name", passed)
        passed = __check_isNone(i, d, "device", "type", passed)        
        # check if all devices with converter apps have two or more links connected
        apps = get_apps_on_device(ict_net, ('device', i))
        if apps is None or apps == []:
            passed = __log_info_and_return_false(" device '" + str(d['name']) + "' (index " + str(i) + ") does not run any apps")            
        if (any([ict_net.app.iloc[a]['type'] == AppType.CONVERTER for a in apps])):
            l = get_links_at(ict_net, ('device', i))
            if len(l) < 2:
                passed = __log_info_and_return_false(" device '" + str(d['name']) + "' (index " + str(i) + ") is running converter type app(s) but has less than two links")                
    return passed

def __is_known_index(ict_net, elt_name, elt_type, elt_idx, target_type, target_idx, passed):
    if target_idx not in ict_net[target_type].index:
        passed = __log_info_and_return_false(str(elt_type)+" '" + str(elt_name) + "' (index " + str(elt_idx) + ") links to non-existing "+str(target_type)+" (index " + str(target_idx) + ")")        
    return passed    

def __inspect_app(ict_net, passed):
    for i, a in ict_net.app.iterrows():
        passed = __check_isNone(i, a, "app", "name", passed, checkempty=True)
        passed = __check_isNone(i, a, "app", "type", passed)        
        passed = __is_known_index(ict_net, a['name'], 'app', i, 'device', a['device'], passed)
        # if a['device'] not in ict_net.device.index:
        #     pilogger.info(" app '" + str(a['name']) + "' (index " + str(i) + ") links to non-existing device (index " + str(a['device']) + ")")
        #     passed = False
    
        # check if Apps with conversions run on converter type devices
        if a['type'] == AppType.CONVERTER:
            d = a.device 
            if ict_net.device.iloc[d]['type'] != DeviceType.CONVERTER:
                passed = __log_info_and_return_false(" Converter-type app '"+str(a['name'])+"' is running on non-converter type device '"+str(ict_net.device.iloc[d]['name'])+"'")                            
    
    return passed


def __inspect_conn(ict_net, passed):
    for i, c in ict_net.conn.iterrows():
        passed = __check_isNone(i, c, "connection", "name", passed, checkempty=True)        
        passed = __is_known_index(ict_net, c['name'], 'connection', i, 'app', c['from'], passed)
        passed = __is_known_index(ict_net, c['name'], 'connection', i, 'app', c['to'], passed)        
    
    return passed

def __inspect_ip(ict_net, passed):
    if "ip_addr" not in ict_net['node'].keys():
        return passed
    # check for double IP addresses (could be intended, warn only)    
    all_ips = [i for i in ict_net['node']['ip_addr']]        # get all node ips, 2d list
    all_ips = [i for sub in all_ips for i in sub]            # flattens list
    all_ips += [i for i in ict_net['device']['ip_addr']]     # add device ips
    duplicates = set([d for d in all_ips if all_ips.count(d)>1])  # get duplicates
    for d in duplicates: 
        passed = __log_info_and_return_false("Warning: found duplicate IP "+str(d))        

    # check if routers have as many ip_addr as netmask and link_types
    for i, n in ict_net.node.iterrows():
        if (n.type == NodeType.ROUTER):
            l = [len(n['ip_addr']), len(n['netmask']), len(n['link_types'])]
            if len(set(l))!=1:
                 passed = __log_info_and_return_false("Warning: node "+str(n['name'])+" has different length ip_addr, netmask and/or link_types")              
                 
    # check for existence of ips in static iptable entries
    if ict_net.iptables is not None:
        for i, t in ict_net.iptables.iterrows():
            if t['destination'] not in all_ips:
                 passed = __log_info_and_return_false("Warning: iptables entry "+str(i)+" has non-existing destination ip "+str(t['destination']))                 
            if t['gateway'] not in all_ips:
                 passed = __log_info_and_return_false("Warning: iptables entry "+str(i)+" has non-existing gateway ip "+str(t['gateway']))                 
    
    return passed


def inspect(ict_net):
    """
    Performs a consistency check on an ict network. This checks if all required parameters are present and all elements
    are well defined, including cross-element relations, e.g. existence of from_elt and to_elt for links etc. 

    :INPUT:
        **ict_net** (pandaictNet) - The pandaict network to check.            
        
    :OUTPUT:
        **passed** (boolean) - True if consistency check passed, False otherwise.  
    
    """
    
    passed = True    
    pilogger.info("----------- pandaICT inspection protocol for ict_net '"+str(ict_net['name'])+"' -----------")
      
    passed = __inspect_node(ict_net, passed)      
    passed = __inspect_link(ict_net, passed)    
    passed = __inspect_device(ict_net, passed)    
    passed = __inspect_app(ict_net, passed)
    passed = __inspect_conn(ict_net, passed)  
    passed = __inspect_ip(ict_net, passed)                     
           
    # check for isolated network areas    
    # check if all connections have at least one possible route (including protocols) 
        
    if passed:
        print("----------- INSPECTION PASSED -----------")
        pilogger.info("----------- INSPECTION PASSED -----------")
    else:        
        print("----------- INSPECTION FAILED -----------")
        pilogger.info("----------- INSPECTION FAILED -----------")        
        
    return passed