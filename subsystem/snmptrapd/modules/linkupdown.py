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

def handleTrap(trap, config=None):

    db = getConnection('default')
    c = db.cursor()

    if trap.genericType in ['LINKUP','LINKDOWN']:
        logger.debug("Module linkupdown got trap %s %s" %(trap.snmpTrapOID, trap.genericType))

        # Initialize eventvariables
        source = 'snmptrapd'
        target = 'eventEngine'
        eventtypeid = 'linkState'

        netboxid = 0
        deviceid = 0
        try:
            query = "SELECT * FROM netbox LEFT JOIN type USING (typeid) WHERE ip = '%s'" %(trap.src)
            logger.debug(query)
            c.execute(query)
            res = c.dictfetchone()

            netboxid = res['netboxid']
            deviceid = res['deviceid']

            if res['vendorid'] == 'hp':
                # Do a new query to get deviceid based on community in trap
                community = trap.community

                if community.find('@'):
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
                
        except Exception, why:
            logger.error("Error when querying database: %s" %why)

        # Get config
        port = ''
        portOID = config.get('linkupdown','portOID')
        for key, val in trap.varbinds.items():
            if key.find(portOID) >= 0:
                port = val


        subid = val
        ending = ""

        # Check for traptype, post event on queue
        if trap.genericType == 'LINKUP':
            state = 'e'
            ending = 'up'

            e = Event(source=source, target=target, netboxid=netboxid, deviceid=deviceid,
                      subid=subid, eventtypeid=eventtypeid, state=state)
            e['alerttype'] = 'linkUp'

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

            try:
                e.post()
            except nav.errors.GeneralException, why:
                logger.error(why)
                return False


        logger.info("Port %s on %s is %s." %(port, trap.src, ending))

        return True
    else:
        return False
