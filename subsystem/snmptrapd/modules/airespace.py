#!/usr/bin/env python

import logging
import nav.errors
logger = logging.getLogger('nav.snmptrapd.airespace')
import nav.db
from nav.event import Event

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"

db = nav.db.getConnection('default')

def handleTrap(trap, config=None):

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

    heartbeatLossTrap = '.1.3.6.1.4.1.14179.2.6.3.88'

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
        if (c.rowcount > 0):
            res = c.dictfetchone()
            netboxid = res['netboxid']
            deviceid = res['deviceid']
        else:
            logger.info("Could not find netbox with ip %s in database, returning" %(trap.src))
            return False
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

    elif oid == heartbeatLossTrap:
        # This trap will be generated when controller loses connection
        # with the Supervisor Switch in which it is physically
        # embedded and doesn't hear the heartbeat keepalives from the
        # Supervisor.

        logger.info("Controller %s reports no connection to supervisor switch" %(trap.src))

        return True
        
    else:
        return False

def postEvent(e):
    
    try:
        e.post()
    except nav.errors.GeneralException, e:
        logger.error(e)
        return False

def verifyEventtype ():
    c = db.cursor()

    sql = """
    INSERT INTO eventtype (
    SELECT 'apState','Tells us whether an access point has disassociated from the controller or associated','y' WHERE NOT EXISTS (
    SELECT * FROM eventtype WHERE eventtypeid = 'apState'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'apState', 'apUp', 'AP associated with controller' WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'apUp'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'apState', 'apDown', 'AP disassociated from controller' WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'apDown'));
    """

    queries = sql.split(';')
    for q in queries:
        if len(q.rstrip()) > 0:
            c.execute(q)

    db.commit()
        

verifyEventtype()
