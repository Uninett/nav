#!/usr/bin/env python

import logging
logger = logging.getLogger('nav.snmptrapd.linkupdown')

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"

def handleTrap(trap, config=None):

    if trap.genericType in ['LINKUP','LINKDOWN']:
        logger.debug("Module linkupdown got trap %s %s" %(trap.snmpTrapOID, trap.genericType))

        # Get config
        port = ''
        portOID = config.get('linkupdown','portOID')
        for key, val in trap.varbinds.items():
            if key.find(portOID) >= 0:
                port = val

        ending = ""
        if trap.genericType == 'LINKUP':
            ending = 'up'
        elif trap.genericType == 'LINKDOWN':
            ending = 'down'

        logger.info("Port %s on %s is %s." %(port, trap.src, ending))

        return True
    else:
        return False
