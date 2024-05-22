'''
# Copyright (c) 2016-2023 by University of Kassel and Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel. All rights reserved.

Created on 23.04.2024

@author: jringelstein
'''

import utils
from pandaict.enums import InfoItem, NodeType, DeviceType, AppType
import logging
logger = logging.getLogger("pandaICT_Core")


def inspect(ict_net):
    
    passed = True
    origlevel = logger.level
    logger.setLevel(logging.INFO)
    logger.info("----------- pandaICT inspection protocol for ict_net '"+str(ict_net['name'])+"' -----------")
    # check if mandatory parameters are present
    # check if all cross-references exist
    # check if cross references point to the right element types    
    for i, n in ict_net.node.iterrows():    
        if n['name'] is None or n['name']=="":
            logger.info(" node with index "+str(i)+" has no name")
            passed = False
        if n['type'] is None:
            logger.info(" node '"+str(n['name'])+"' (index "+str(i)+") has no type")
            passed = False
        if n['link_types'] is None:
            logger.info(" node '"+str(n['name'])+"' (index "+str(i)+") has no link_types")
            passed = False   
        # check if all nodes have two or more links connected
        l = utils.get_links_at(ict_net, ('node', i))
        if len(l)<2:
            logger.info(" node '"+str(n['name'])+"' (index "+str(i)+") has less than two links")
            passed = False  
    for i, l in ict_net.link.iterrows():
        if l['name'] is None or l['name']=="":
            logger.info(" Link with index "+str(i)+" has no name")
            passed = False
        if l['type'] is None:
            logger.info(" Link '"+str(l['name'])+"' (index "+str(i)+") has no type")
            passed = False
        # from_elt and to_elt existence and non-equality are tested during creation
    for i, d in ict_net.device.iterrows():
        if d['name'] is None or d['name']=="":
            logger.info(" device with index "+str(i)+" has no name")
            passed = False
        if d['type'] is None:
            logger.info(" device '"+str(d['name'])+"' (index "+str(i)+") has no type")
            passed = False
        # check if all devices with converter apps have two or more links connected
        apps = utils.get_apps_on_device(ict_net, ('device', i))
        if apps is None or apps==[]:
            logger.info(" device '"+str(d['name'])+"' (index "+str(i)+") does not run any apps")
            passed = False
        if (any([ict_net.app.iloc[a]['type']==AppType.CONVERTER for a in apps])):
            l = utils.get_links_at(ict_net, ('device', i))
            if len(l)<2:
                logger.info(" device '"+str(d['name'])+"' (index "+str(i)+") is running converter type app(s) but has less than two links")
                passed = False
    
    for i, a in ict_net.app.iterrows():
        if a['name'] is None or a['name']=="":
            logger.info(" app with index "+str(i)+" has no name")
            passed = False
        if a['type'] is None:
            logger.info(" app '"+str(a['name'])+"' (index "+str(i)+") has no type")
            passed = False
        if a['device'] not in ict_net.device.index:
            logger.info(" app '"+str(a['name'])+"' (index "+str(i)+") links to non-existing device (index "+str(a['device'])+")")
            passed = False
    
    for i, c in ict_net.conn.iterrows():
        if c['name'] is None or c['name']=="":
            logger.info(" connection with index "+str(i)+" has no name")
            passed = False       
        if c['from'] not in ict_net.app.index:
            logger.info(" connection '"+str(c['name'])+"' (index "+str(i)+") links to non existing from_app (index "+str(c['from'])+")")
            passed = False
        if c['to'] not in ict_net.app.index:
            logger.info(" connection '"+str(c['name'])+"' (index "+str(i)+") links to non existing to_app (index "+str(c['to'])+")")
            passed = False
        
    # check for double linkage (excluding multicasts)
    for i, l in ict_net.link.iterrows():
        from_elt = l["from"]
        to_elt   = l["to"]
        linklist = utils.get_links_between(ict_net, from_elt, to_elt)
        if len(linklist) > 1: 
            linklist.remove(i)
            logger.info(" link '"+str(l['name'])+"' (index "+str(i)+") has duplicate(s) (indexes "+str(linklist)+")")
            passed = False
    
    # check std types
    for linktype in ict_net.std_types['link'].keys():
        protocols = ict_net.std_types['link'][linktype]['protocols']
        for p in protocols:
            if p not in ict_net.std_types['protocol'].keys():
                logger.info(" std link type '"+str(linktype)+"' has unknown protocol '"+str(p)+"'")
                passed = False
         
    # check if Apps with conversions run on converter type devices
    for i, a in ict_net.app.iterrows():
        if a['type'] == AppType.CONVERTER:
            d = a.device 
            if not ict_net.device.iloc[d]['type'] == DeviceType.CONVERTER:
                logger.info(" Converter-type app '"+str(a['name'])+"' is running on non-converter type device '"+str(ict_net.device.iloc[d]['name'])+"'")
                passed = False
           
    # check for isolated network areas    
    # check if all connections have at least one possible route (including protocols) 
        
    if passed:
        print("----------- INSPECTION PASSED -----------")
        logger.info("----------- INSPECTION PASSED -----------")
    else:        
        print("----------- INSPECTION FAILED -----------")
        logger.info("----------- INSPECTION FAILED -----------")        
        
    logger.setLevel(origlevel)    
    return passed