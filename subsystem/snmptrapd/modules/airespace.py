#!/usr/bin/env python

import logging
logger = logging.getLogger('nav.snmptrapd.airespace')

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"

def handleTrap(trap, config=None):

    bsnAPCurrentChannelChanged = '.1.3.6.1.4.1.14179.2.6.3.16'
    bsnAPChannelNumberTrapVariable = '.1.3.6.1.4.1.14179.2.6.2.23'
    bsnAPMacAddrTrapVariable = '.1.3.6.1.4.1.14179.2.6.2.20'

    bsnSignatureAttackDetected = '.1.3.6.1.4.1.14179.2.6.3.70'
    bsnSignatureDescription = '.1.3.6.1.4.1.14179.2.6.2.57'
    bsnAPName = '.1.3.6.1.4.1.14179.2.2.1.1.3'
    bsnSignatureAttackerMacAddress = '.1.3.6.1.4.1.14179.2.6.2.64'

    oid = trap.snmpTrapOID

    if oid == bsnAPCurrentChannelChanged:
        for key, val in trap.varbinds.items():
            if key.find(bsnAPChannelNumberTrapVariable) >= 0:
                channel = val
            elif key.find(bsnAPMacAddrTrapVariable) >= 0:
                mac = val

        logger.info("%s changed channel to %s" %(mac, channel))
        
        return True
    elif oid == bsnSignatureAttackDetected:
        for key, val in trap.varbinds.items():
            if key.find(bsnSignatureDescription) >= 0:
                signature = val
            elif key.find(bsnAPName) >= 0:
                apname = val
            elif key.find(bsnSignatureAttackerMacAddress) >= 0:
                attacker = val

        logger.info("%s discovered signatureattack with description '%s' from %s" %(apname, signature, attacker))
        return True
        
    else:
        return False
