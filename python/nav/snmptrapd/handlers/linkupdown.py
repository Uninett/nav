#
# Copyright 2007, 2010 (C) Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""NAV snmptrapd handler plugin to handle LINKUP and LINKDOWN traps from
network equipment.

"""
import logging
import nav.errors
import re
import psycopg2.extras

from nav.db import getConnection
from nav.event import Event

logger = logging.getLogger('nav.snmptrapd.linkupdown')

def handleTrap(trap, config=None):
    """
    handleTrap is run by snmptrapd every time it receives a
    trap. Return False to signal trap was discarded, True if trap was
    accepted.
    """
    db = getConnection('default')
    c = db.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Linkstate-traps are generictypes. Check for linkup/down and post
    # events on eventq.
    if trap.genericType in ['LINKUP','LINKDOWN']:
        logger.debug("Module linkupdown got trap %s %s" % (trap.snmpTrapOID,
                                                           trap.genericType))

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
            query = """SELECT netboxid, vendorid
                       FROM netbox
                       LEFT JOIN type USING (typeid)
                       WHERE ip = %s"""
            logger.debug(query)
            c.execute(query, (trap.agent,))
            res = c.fetchone()

            netboxid = res['netboxid']

            module = '0'

        except Exception, why:
            logger.error("Error when querying database: %s" %why)


        # Find interfaceid
        idquery = """SELECT
                       interfaceid, module.deviceid,
                       module.name AS modulename,
                       interface.ifname, interface.ifalias
                     FROM netbox
                     JOIN interface USING (netboxid)
                     LEFT JOIN module USING (moduleid)
                     WHERE ip=%s AND ifindex = %s"""
        logger.debug(idquery)
        try:
            c.execute(idquery, (trap.agent, ifindex))
        except nav.db.driver.ProgrammingError, why:
            logger.error(why)
            return False

        # If no rows returned, exit
        if c.rowcount < 1:
            logger.debug('Could not find ifindex %s on %s'
                         %(ifindex, trap.src))
            return False
        
        idres = c.fetchone()

        # Subid is interfaceid in this case
        subid = idres['interfaceid']
        interface = idres['ifname']
        module = idres['modulename']
        ifalias = idres['ifalias']

        # The deviceid of the module containing the port
        deviceid = idres['deviceid']

        # Todo: Make sure the events are actually forwarded to alertq
        # for alerting.  It seems like the BoxState-handlerplugin of
        # eventEngine accepts this event but does nothing with it.
        # Thus an alert will never trigger of the events.

        # Check for traptype, post event on queue        
        if trap.genericType == 'LINKUP':
            state = 'e'
            ending = 'up'

            e = Event(source=source, target=target, netboxid=netboxid,
                      deviceid=deviceid, subid=subid, eventtypeid=eventtypeid,
                      state=state)
            e['alerttype'] = 'linkUp'
            e['module'] = module
            e['interface'] = interface
            e['ifalias'] = ifalias

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
            e['interface'] = interface
            e['ifalias'] = ifalias

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
    """
    Safe way of verifying that the event- and alarmtypes exist in the
    database. Should be run when module is imported.
    """
    db = getConnection('default')
    c = db.cursor()

    sql = """
    INSERT INTO eventtype (
    SELECT 'linkState','Tells us whether a link is up or down.','y'
    WHERE NOT EXISTS (
    SELECT * FROM eventtype WHERE eventtypeid = 'linkState'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'linkState', 'linkUp',
    'Link active'
    WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'linkUp'));

    INSERT INTO alertType (
    SELECT nextval('alerttype_alerttypeid_seq'), 'linkState', 'linkDown',
    'Link inactive'
    WHERE NOT EXISTS (
    SELECT * FROM alerttype WHERE alerttype = 'linkDown'));
    """

    queries = sql.split(';')
    for q in queries:
        if len(q.rstrip()) > 0:
            c.execute(q)

    db.commit()
        

# Run verifyeventtype at import
verifyEventtype()
