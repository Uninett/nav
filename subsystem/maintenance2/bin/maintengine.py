#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
# Copyright 2003-2005 Norwegian University of Science and Technology
# Copyright 2006 UNINETT AS
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
#          Stein Magnus Jodal <stein.magnus@jodal.no>, 2006
#

"""
This program dispatches maintenance events according to the maintenance
schedule in NAVdb.
"""

__copyright__ = "Copyright 2003-2005 NTNU, 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Bjørn Ove Grøtan (bjorn.grotan@itea.ntnu.no), Sigurd Gartmann (sigurd-nav@brogar.org), Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id:$"

import sys
import nav.db
import nav.event
from mx import DateTime

# Placeholders
events = []
states = ['scheduled', 'active', 'passed', 'overridden']
debug = False
boxesOffMaintenance = []
connection = nav.db.getConnection('eventEngine', 'manage')
connection.autocommit(0)
# Make sure isolation level is "read committed", not "serialized"
connection.set_isolation_level(1)
database = connection.cursor()


def schedule():
    """Check if there are maintenance tasks to be schedule"""

    sql = """UPDATE maint_task SET state = 'scheduled'
        WHERE state IS NULL
        OR state NOT IN ('scheduled', 'active', 'passed', 'overridden')"""
    database.execute(sql)
    connection.commit()
    

def check_state():
    """Checks if there are some maintenance tasks to be set active or
    passed."""

    sql = """SELECT maint_taskid FROM maint_task
        WHERE maint_start < NOW() AND state = 'scheduled'"""
    database.execute(sql)
    for (taskid) in database.fetchall():
        e = {}
        e['type'] = 'active'
        e['taskid'] = taskid
        events.append(e)
        
    sql = """SELECT maint_taskid FROM maint_task
        WHERE maint_end < NOW() AND state = 'active'"""
    database.execute(sql)
    for (taskid) in database.fetchall():
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
        database.execute(sql, data)
    
        for (key, val) in database.fetchall():
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
                        WHERE locationid = %(locationid)d"""
                    data = { 'locationid': value }
                    database.execute(sql, data)
                elif key == 'room':
                    sql = """SELECT netboxid, sysname, deviceid
                        FROM netbox
                        WHERE roomid = %(roomid)d"""
                    data = { 'roomid': value }
                    database.execute(sql, data)
                for (netboxid, sysname, deviceid) in database.fetchall():
                    netboxes.append({ 'netboxid': netboxid,
                                      'sysname': sysname,
                                      'deviceid': deviceid,
                                      'qvar': 'netbox',
                                      'qvar': sysname })
            elif key == 'netbox':
                sql = """SELECT netboxid, sysname, deviceid
                    FROM netbox
                    WHERE netboxid = %(netboxid)d"""
                data = { 'netboxid': value }
                database.execute(sql, data)
                result = database.fetchone()
                if result:
                    (netboxid, sysname, deviceid) = result
                    netboxes.append({ 'netboxid': netboxid,
                                      'sysname': sysname,
                                      'deviceid': deviceid,
                                      'qvar': 'netbox',
                                      'qval': sysname })
            elif key == 'service':
                sql = """SELECT netboxid, sysname, deviceid, handler
                    FROM service INNER JOIN netbox USING (netboxid)
                    WHERE serviceid = %(serviceid)d"""
                data = { 'serviceid': value }
                database.execute(sql, data)
                result = database.fetchone()
                if result:
                    (netboxid, sysname, deviceid, handler) = result
                    netboxes.append({ 'netboxid': netboxid,
                                      'sysname': sysname,
                                      'deviceid': deviceid,
                                      'serviceid': value,
                                      'servicename': handler,
                                      'qvar': 'service',
                                      'qval': handler })
            elif key == 'module':
                # Unsupported as of NAV 3.2
                raise "Deprecated component key" # FIXME: Should be class
            else:
                raise "Unsupported component key" # FIXME: Should be class

           
            # Create events for all related netboxes
            for netbox in netboxes:
                # Append to list of boxes taken off maintenance during this run
                if type == 'passed':
                    boxesOffMaintenance.append(netbox['netboxid'])
 
                if netbox['serviceid']:
                    subid = netbox['serviceid']
                else:
                    subid = None

                # Create event
                event = nav.event.Event.Event(source=source, target=target,
                    deviceid=netbox['deviceid'],
                    netboxid=netbox['netboxid'], subid=subid,
                    eventtypeid=eventtype, state=state, value=value,
                    severity=severity)
                event['var'] = netbox['qvar']
                event['val'] = netbox['qval']

                # Add event to eventq
                event.post()

        # Update state
        sql = """UPDATE maint_task
            SET state = %(state)s
            WHERE maint_taskid = %(maint_taskid)d"""
        data = { 'state': type,
                 'maint_taskid': taskid }
        database.execute(sql, data)

        # Commit transaction
        connection.commit()


def remove_forgotten():
    """
    Remove 'forgotten' netboxes from their maintenance state.

    Sometimes, like when netboxes have been deleted from a maintenance task
    during its active maintenance window, we will no longer know that the box
    has gone on maintenenance and should be taken off. This function takes all
    'forgotten' netboxes off maintenance.

    """

    # This SQL retrieves a list of boxes that are supposed to be on
    # maintenance, according to the schedule.
    sched = """SELECT n.netboxid, n.deviceid, n.sysname
            FROM maint m INNTER JOIN netbox n ON (n.netboxid = m.value)
            WHERE m.key = 'netbox' AND m.state = 'active'

            UNION

            SELECT n.netboxid, n.deviceid, n.sysname
            FROM maint m INNER JOIN netbox n ON (n.roomid = m.value)
            WHERE m.key = 'netbox' AND m.state = 'active'

            UNION
    
            SELECT n.netboxid, n.deviceid, n.sysname
            FROM maint m INNER JOIN netbox n ON (n.roomid IN
                (SELECT roomid FROM room WHERE locationid = m.value)
            WHERE m.key = 'location' AND m.state = 'active'

            UNION

            SELECT n.netboxid, n.deviceid, n.sysname
            FROM maint m INNER JOIN netbox n ON (n.netboxid IN
                (SELECT netboxid FROM service WHERE serviceid = m.value)
            WHERE m.key = 'service' AND m.state = 'active'"""

    # This SQL retrieves a list of boxes that are currently on
    # maintenance, according to the alert history.
    actual = """SELECT n.netboxid, n.deviceid, n.sysname
        FROM alerthist a LEFT JOIN netbox n USING (netboxid)
        WHERE eventtypeid='maintenanceState' AND netboxid IS NOT NULL
        AND end_time = 'infinity'"""

    # The full SQL is a set operation to select all boxes that are
    # currently on maintenance and subtracts those that are supposed
    # to be on maintenance - resulting in a list of boxes that should
    # be taken off maintenance immediately.
    fullSQL = "(%s) \n EXCEPT \n (%s)" % (actual, sched)
    database.execute(fullSQL);

    target = 'eventEngine'
    subsystem = 'maintenance'
    source = subsystem
    severity = 50
    eventtype = 'maintenanceState'
    state = 'e'
    value = 0

    for (netboxid, deviceid, sysname) in database.fetchall():
        if netboxid in boxesOffMaintenance:
            # MaintenenceOff-events posted during this run might not
            # have been processed by eventEngine yet. We discard these
            # boxes here.
            continue

        print >> sys.stderr, ("Box %s (%d) was on unscheduled " +
                              "maintenance, taking off maintenance now...") % \
                              (sysname, netboxid)

        # FIXME: If it's a service, we have to set subid also
        subid = None

        # Create event
        event = nav.event.Event.Event(source=source, target=target,
            deviceid=deviceid, netboxid=netboxid, subid=subid,
            eventtypeid=eventtype, state=state, value=value, severity=severity)
        event['var'] = 'netbox'
        event['val'] = sysname

    # Commit transaction
    connection.commit()


if __name__ == '__main__':
    schedule()
    check_state()
    send_event()
    remove_forgotten()
