#!/usr/bin/env python

import logging
import nav.errors
logger = logging.getLogger('nav.snmptrapd.airespace')
import nav.db
from nav.event import Event

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"

def handleTrap(trap, config=None):

    db = nav.db.getConnection('default')
    c = db.cursor()

    bsnAPCurrentChannelChanged = '.1.3.6.1.4.1.14179.2.6.3.16'
    bsnAPChannelNumberTrapVariable = '.1.3.6.1.4.1.14179.2.6.2.23'
    bsnAPMacAddrTrapVariable = '.1.3.6.1.4.1.14179.2.6.2.20'

    bsnSignatureAttackDetected = '.1.3.6.1.4.1.14179.2.6.3.70'
    bsnSignatureDescription = '.1.3.6.1.4.1.14179.2.6.2.57'
    bsnAPName = '.1.3.6.1.4.1.14179.2.2.1.1.3'
    bsnSignatureAttackerMacAddress = '.1.3.6.1.4.1.14179.2.6.2.64'

    bsnAPDisassociated = '.1.3.6.1.4.1.14179.2.6.3.8'
    bsnAPIfUp = '.1.3.6.1.4.1.14179.2.6.3.9'
    bsnAPDot3MacAddress = '.1.3.6.1.4.1.14179.2.2.1.1.1'

    oid = trap.snmpTrapOID

    # Init eventvariables
    source = 'snmptrapd'
    target = 'eventEngine'
    eventtypeid = 'apState'
    
    netboxid = 0
    try:
        query = "SELECT * FROM netbox WHERE ip = '%s'" %(trap.src)
        #logger.debug(query)
        c.execute(query)
        res = c.dictfetchone()
        netboxid = res['netboxid']
        deviceid = res['deviceid']
    except Exception, why:
        logger.exception("Error when querying database: %s" %why)
        return False


    if oid == bsnAPCurrentChannelChanged:
        for key, val in trap.varbinds.items():
            if key.find(bsnAPChannelNumberTrapVariable) >= 0:
                channel = val
            elif key.find(bsnAPMacAddrTrapVariable) >= 0:
                mac = val

        #logger.info("%s changed channel to %s" %(mac, channel))
        
        return True
    elif oid == bsnSignatureAttackDetected:
        for key, val in trap.varbinds.items():
            if key.find(bsnSignatureDescription) >= 0:
                signature = val
            elif key.find(bsnAPName) >= 0:
                apname = val
            elif key.find(bsnSignatureAttackerMacAddress) >= 0:
                attacker = val

        #logger.info("%s discovered signatureattack with description '%s' from %s" %(apname, signature, attacker))
        return True

    elif oid == bsnAPDisassociated:
        # Controller sent message about ap that disassociated
        # At the moment we just have mac-address of AP (this is to be fixed
        # in future releases of controller software)
        for key, val in trap.varbinds.items():
            if key.find(bsnAPMacAddrTrapVariable) >= 0:
                mac = val

        logger.info("AP with mac %s disassociated" %(mac))

        state = 's'

        e = Event(source=source, target=target, netboxid=netboxid,
                  eventtypeid=eventtypeid, state=state)
        e['alerttype'] = 'apDown'
        e['mac'] = mac

        postEvent(e)
        return True

    elif oid == bsnAPIfUp:
        # Controller sent message about ap that associated.
        # At the moment we just have mac-address of AP (this is to be fixed
        # in future releases of controller software)
        for key, val in trap.varbinds.items():
            if key.find(bsnAPDot3MacAddress) >= 0:
                mac = val

        logger.info("AP with mac %s associated" %(mac))

        state = 'e'

        e = Event(source=source, target=target, netboxid=netboxid,
                  eventtypeid=eventtypeid, state=state)
        e['alerttype'] = 'apUp'
        e['mac'] = mac

        postEvent(e)

        return True

        
    else:
        return False

def postEvent(e):
    
    try:
        e.post()
    except nav.errors.GeneralException, e:
        logger.error(e)
        return False
