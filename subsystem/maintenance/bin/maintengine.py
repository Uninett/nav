#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
# Copyright 2003-2005 Norwegian University of Science and Technology
# Copyright 2006, 2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Authors: Bjørn Ove Grøtan <bjorn.grotan@itea.ntnu.no>, 2003
#          Sigurd Gartmann <sigurd-nav@brogar.org>, 2004
#          Stein Magnus Jodal <stein.magnus.jodal@uninett.no>, 2006
#

"""
This program dispatches maintenance events according to the maintenance
schedule in NAVdb.
"""

__copyright__ = "Copyright 2003-2005 NTNU, 2006-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Bjørn Ove Grøtan (bjorn.grotan@itea.ntnu.no), Sigurd Gartmann (sigurd-nav@brogar.org), Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id$"

import logging
import os.path
import sys
import nav.db
import nav.event
import nav.logs

logfile = os.path.join(nav.path.localstatedir, 'log', 'maintengine.log')
logformat = "[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s"
logger = logging.getLogger('maintengine')

# Placeholders
events = []
states = ['scheduled', 'active', 'passed', 'canceled']
debug = False
boxesOffMaintenance = []

dbconn = nav.db.getConnection('eventEngine', 'manage')
# Make sure isolation level is "read committed", not "serialized"
dbconn.set_isolation_level(1)
db = dbconn.cursor()


def loginit():
    """Initialize logging setup"""

    global _loginited
    try:
        # Make sure we don't initialize logging setup several times (in case
        # of module reloads and such)
        if _loginited:
            return
    except:
        pass

    root = logging.getLogger('')

    formatter = logging.Formatter(logformat)
    try:
        handler = logging.FileHandler(logfile)
    except IOError, e:
        # Most likely, we were denied access to the log file.
        # We silently ignore it and log nothing :-P
        pass
    else:
        handler.setFormatter(formatter)
        root.addHandler(handler)
        nav.logs.setLogLevels()
        _loginited = True


def schedule():
    """Check if there are maintenance tasks to be schedule"""

    sql = """UPDATE maint_task SET state = 'scheduled'
        WHERE state IS NULL
        OR state NOT IN ('scheduled', 'active', 'passed', 'canceled')"""
    db.execute(sql)
    dbconn.commit()
    

def check_state():
    """Checks if there are some maintenance tasks to be set active or
    passed."""

    sql = """SELECT maint_taskid FROM maint_task
        WHERE maint_start < NOW() AND state = 'scheduled'"""
    db.execute(sql)
    for (taskid,) in db.fetchall():
        e = {}
        e['type'] = 'active'
        e['taskid'] = taskid
        events.append(e)
        
    sql = """SELECT maint_taskid FROM maint_task
        WHERE maint_end < NOW() AND state = 'active'"""
    db.execute(sql)
    for (taskid,) in db.fetchall():
        e = {}
        e['type'] = 'passed'
        e['taskid'] = taskid
        events.append(e)

    # FIXME: Create some magic to check overlapping timeframes with overlapping
    # components


def send_event():
    """Sends events to the event queue."""

    for e in events:
        type = e['type']
        taskid = e['taskid']

        # Get all components related to task/event
        sql = """SELECT key, value FROM maint_component
                 WHERE maint_taskid = %(maint_taskid)d"""
        data = { 'maint_taskid': taskid }
        db.execute(sql, data)
    
        for (key, val) in db.fetchall():
            # Prepare event variables
            target = 'eventEngine'
            subsystem = 'maintenance'
            source = subsystem
            severity = 50
            eventtype = 'maintenanceState'
            if type == 'active':
                state = 's' # s = start
                value = 100
            elif type == 'passed':
                state = 'e' # e = end
                value = 0

            # Get all related netboxes
            netboxes = []
            if key in ('location', 'room'):
                if key == 'location':
                    sql = """SELECT netboxid, sysname, deviceid
                        FROM netbox INNER JOIN room USING (roomid)
                        WHERE locationid = %(locationid)s"""
                    data = { 'locationid': val }

                    logger.debug("location query: %s", sql % data)
                    db.execute(sql, data)
                    logger.debug("location number of results: %d", db.rowcount)
                elif key == 'room':
                    sql = """SELECT netboxid, sysname, deviceid
                        FROM netbox
                        WHERE roomid = %(roomid)s"""
                    data = { 'roomid': val }

                    logger.debug("room query: %s", sql % data)
                    db.execute(sql, data)
                    logger.debug("room number of results: %d", db.rowcount)

                for (netboxid, sysname, deviceid) in db.fetchall():
                    netboxes.append({ 'netboxid': netboxid,
                                      'sysname': sysname,
                                      'deviceid': deviceid,
                                      'cvar': 'netbox',
                                      'cval': sysname })
            elif key == 'netbox':
                sql = """SELECT netboxid, sysname, deviceid
                    FROM netbox
                    WHERE netboxid = %(netboxid)d"""
                data = { 'netboxid': int(val) }

                logger.debug("netbox query: %s", sql % data)
                db.execute(sql, data)
                logger.debug("netbox number of results: %d", db.rowcount)
                result = db.fetchone()

                if result:
                    (netboxid, sysname, deviceid) = result
                    netboxes.append({ 'netboxid': netboxid,
                                      'sysname': sysname,
                                      'deviceid': deviceid,
                                      'cvar': 'netbox',
                                      'cval': sysname })
            elif key == 'service':
                sql = """SELECT netboxid, sysname, deviceid, handler
                    FROM service INNER JOIN netbox USING (netboxid)
                    WHERE serviceid = %(serviceid)d"""
                data = { 'serviceid': int(val) }

                logger.debug("service query: %s", sql % data)
                db.execute(sql, data)
                logger.debug("service number of results: %d", db.rowcount)
                result = db.fetchone()

                if result:
                    (netboxid, sysname, deviceid, handler) = result
                    netboxes.append({ 'netboxid': netboxid,
                                      'sysname': sysname,
                                      'deviceid': deviceid,
                                      'serviceid': int(val),
                                      'servicename': handler,
                                      'cvar': 'service',
                                      'cval': handler })
            elif key == 'module':
                # Unsupported as of NAV 3.2
                raise DeprecationWarning, "Deprecated component key"

            # Create events for all related netboxes
            for netbox in netboxes:
                # Append to list of boxes taken off maintenance during this run
                if type == 'passed':
                    boxesOffMaintenance.append(netbox['netboxid'])
 
                if netbox.has_key('serviceid'):
                    subid = netbox['serviceid']
                else:
                    subid = None

                # Create event
                event = nav.event.Event(source=source, target=target,
                    deviceid=netbox['deviceid'],
                    netboxid=netbox['netboxid'], subid=subid,
                    eventtypeid=eventtype, state=state, value=value,
                    severity=severity)
                event[netbox['cvar']] = netbox['cval']
                event['maint_taskid'] = taskid

                # Add event to eventq
                result = event.post()
                logger.debug("Event: %s, Result: %s", event, result)

        # Update state
        sql = """UPDATE maint_task
            SET state = %(state)s
            WHERE maint_taskid = %(maint_taskid)d"""
        data = { 'state': type,
                 'maint_taskid': taskid }
        db.execute(sql, data)

        # Commit transaction
        dbconn.commit()


def remove_forgotten():
    """
    Remove 'forgotten' netboxes from their maintenance state.

    Sometimes, like when netboxes have been deleted from a maintenance task
    during its active maintenance window, we will no longer know that the box
    has gone on maintenenance and should be taken off. This function takes all
    'forgotten' netboxes off maintenance.

    """

    # This SQL retrieves a list of boxes that are currently on
    # maintenance, according to the alert history.
    sqlactual = """SELECT ah.netboxid, ah.deviceid, n.sysname, subid 
        FROM alerthist ah LEFT JOIN netbox n USING (netboxid)
        WHERE eventtypeid='maintenanceState' AND netboxid IS NOT NULL
        AND end_time = 'infinity'"""

    # This SQL retrieves a list of boxes that are supposed to be on
    # maintenance, according to the schedule.
    sqlsched = """SELECT n.netboxid, n.deviceid, n.sysname, NULL AS subid
        FROM maint m INNER JOIN netbox n ON (n.netboxid::text = m.value)
        WHERE m.key = 'netbox' AND m.state = 'active'

        UNION

        SELECT n.netboxid, n.deviceid, n.sysname, NULL AS subid
        FROM maint m INNER JOIN netbox n ON (n.roomid = m.value)
        WHERE m.key = 'room' AND m.state = 'active'

        UNION

        SELECT n.netboxid, n.deviceid, n.sysname, NULL AS subid
        FROM maint m INNER JOIN netbox n ON (n.roomid IN
            (SELECT roomid FROM room WHERE locationid = m.value))
        WHERE m.key = 'location' AND m.state = 'active'

        UNION
        
        SELECT n.netboxid, n.deviceid, n.sysname, m.value AS subid
        FROM maint m INNER JOIN netbox n ON (n.netboxid IN
            (SELECT netboxid FROM service WHERE
                serviceid::text LIKE m.value))
        WHERE m.key = 'service' AND m.state = 'active'"""

    # The full SQL is a set operation to select all boxes that are
    # currently on maintenance and subtracts those that are supposed
    # to be on maintenance - resulting in a list of boxes that should
    # be taken off maintenance immediately.
    sqlfull = "(%s) \n EXCEPT \n (%s)" % (sqlactual, sqlsched)
    db.execute(sqlfull)

    target = 'eventEngine'
    subsystem = 'maintenance'
    source = subsystem
    severity = 50
    eventtype = 'maintenanceState'
    state = 'e'
    value = 0

    for (netboxid, deviceid, sysname, subid) in db.fetchall():
        if netboxid in boxesOffMaintenance:
            # MaintenenceOff-events posted during this run might not
            # have been processed by eventEngine yet. We discard these
            # boxes here.
            continue

        # If it's a service, we have to set subid also
        if subid is None:
            logger.info("Box %s (%d) is on unscheduled maintenance. " +
                        "Taking off maintenance now.", sysname, netboxid)
            subid = False
        else:
            logger.info("Service (%d) at box %s (%d) is on unscheduled " +
                        "maintenance. Taking off maintenance...",
                        subid, sysname, netboxid)
            subid = int(subid)

        # Create event
        event = nav.event.Event(source=source, target=target,
            deviceid=deviceid, netboxid=netboxid, subid=subid,
            eventtypeid=eventtype, state=state, value=value, severity=severity)

        result = event.post()
        logger.debug("Event: %s, Result: %s", event, result)

    # Commit transaction
    dbconn.commit()


if __name__ == '__main__':
    loginit()
    schedule()
    check_state()
    send_event()
    remove_forgotten()
