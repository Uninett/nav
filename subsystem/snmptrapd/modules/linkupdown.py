#!/usr/bin/env python

import logging
import nav.errors
import re
from nav.db import getConnection
from nav.event import Event

logger = logging.getLogger('nav.snmptrapd.linkupdown')

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal (john.m.bredal@ntnu.no)"


global db
db = getConnection('default')


def handleTrap(trap, config=None):

    c = db.cursor()

    if trap.genericType in ['LINKUP','LINKDOWN']:
        logger.debug("Module linkupdown got trap %s %s" %(trap.snmpTrapOID, trap.genericType))

        # Initialize eventvariables
        source = 'snmptrapd'
        target = 'eventEngine'
        eventtypeid = 'linkState'

        ifindex = ''
        portOID = config.get('linkupdown','portOID')
        for key, val in trap.varbinds.items():
            if key.find(portOID) >= 0:
                ifindex = val


        netboxid = 0
        deviceid = 0

        # Find netbox and deviceid for this ip-address.
        try:
            query = "SELECT * FROM netbox LEFT JOIN type USING (typeid) WHERE ip = '%s'" %(trap.src)
            logger.debug(query)
            c.execute(query)
            res = c.dictfetchone()

            netboxid = res['netboxid']
            deviceid = res['deviceid']

            module = '0'
            if res['vendorid'] == 'hp':
                # Do a new query to get deviceid based on community in trap
                community = trap.community

                if community.find('@') >= 0:
                    try:
                        logger.debug("Moduleinfo %s" %community)
                        module = re.search('\@sw(\d+)', community).groups()[0]
                    except Exception, e:
                        # Didn't find a match for module, can't handle trap
                        logger.debug("No match for module, returning")
                        return False
                
                    # Get correct deviceid
                    deviceq = "SELECT * FROM module WHERE netboxid=%s AND module=%s" %(netboxid, module)
                    c.execute(deviceq)
                    r = c.dictfetchone()
                    deviceid = r['deviceid']

                # Ugly hack to find nav's ifindex
                ifindex = "%s%02d" %(str(int(module) + 1), int(ifindex))

                
        except Exception, why:
            logger.error("Error when querying database: %s" %why)


        # Find swportid
        idquery = "SELECT * FROM netbox LEFT JOIN module USING (netboxid) LEFT JOIN swport USING (moduleid) WHERE ip='%s' AND ifindex = %s" %(trap.src, ifindex)
        logger.debug(idquery)
        c.execute(idquery)
        idres = c.dictfetchone()

        # Subid is swportid in this case
        subid = idres['swportid']

        # Todo: Make sure the events are actually forwarded to alertq
        # for alerting.  It seems like the BoxState-handlerplugin of
        # eventEngine accepts this event but does nothing with it.
        # Thus an alert will never trigger of the events.

        # Check for traptype, post event on queue        
        if trap.genericType == 'LINKUP':
            state = 'e'
            ending = 'up'

            e = Event(source=source, target=target, netboxid=netboxid, deviceid=deviceid,
                      subid=subid, eventtypeid=eventtypeid, state=state)
            e['alerttype'] = 'linkUp'
            e['module'] = module

            try:
                e.post()
            except nav.errors.GeneralException, why:
                logger.error(why)
                return False
            
        elif trap.genericType == 'LINKDOWN':
            state = 's'
            ending = 'down'

            e = Event(source=source, target=target, netboxid=netboxid,
                      deviceid=deviceid, subid=subid,
                      eventtypeid=eventtypeid, state=state)

            e['alerttype'] = 'linkDown'
            e['module'] = module

            try:
                e.post()
            except nav.errors.GeneralException, why:
                logger.error(why)
                return False


        logger.info("Ifindex %s on %s is %s." %(ifindex, trap.src, ending))

        return True
    else:
        return False


def verifyEventtype ():
    c = db.cursor()

    sql = """
    INSERT INTO eventtype (
    SELECT 'linkState','Tells us whether a link is up or down.','y' WHERE NOT EXISTS (
    SELECT * FROM eventtype WHERE eventtypeid = 'linkState'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'linkState', 'linkUp', 'Link active' WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'linkUp'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'linkState', 'linkDown', 'Link inactive' WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'linkDown'));
    """

    queries = sql.split(';')
    for q in queries:
        if len(q.rstrip()) > 0:
            c.execute(q)

    db.commit()
        

verifyEventtype()
