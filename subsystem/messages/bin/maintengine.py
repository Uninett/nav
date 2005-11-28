#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-
#
# Copyright 2003-2005 Norwegian University of Science and Technology
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
# $Id$
# Authors: Bjørn Ove Grøtan <bjorn.grotan@itea.ntnu.no>, 2003
#          Sigurd Gartmann <sigurd-nav@brogar.org>, 2004
#
"""This program dispatches maintenance events according to the
maintenance schedule in NAVdb.
"""
import sys
from nav import db
from mx import DateTime

##
# some placeholders
events = []
states = ['scheduled','active','passed','overridden']
debug = False
boxesOffMaintenance = []
connection = db.getConnection('eventEngine','manage')
connection.autocommit(0)
# Make sure isolation level is "read committed", not "serialized"
connection.set_isolation_level(1)
database = connection.cursor()


def schedule():
    """ Check if there are maintenances to be schedule """
    sql = "update maintenance set state = 'scheduled' where state is null or state not in ('scheduled','active','passed','overridden')"
    database.execute(sql)
    connection.commit()
    

def check_state():
    """ 
    Checks if there are some maintenances to be set active 
    (e.g. send maintenenaceOn)
    """
    sql = "select maintenanceid,emotdid from maintenance where maint_start < now() and state='scheduled'"
    database.execute(sql)
    for (mid,emotdid) in database.fetchall():
        e = {}
        e['type'] = 'active'
        e['emotdid'] = emotdid
        e['maintenanceid'] = mid
        events.append(e)
        
    sql = "select maintenanceid,emotdid from maintenance where maint_end < now() and state='active'"
    database.execute(sql)
    for (mid,emotdid) in database.fetchall():
        e = {}
        e['type'] = 'passed'
        e['emotdid'] = emotdid
        e['maintenanceid'] = mid
        events.append(e)
    # bør ha magi for å sjekke overlappende tidsvinduer med overlappende bokser... jeje


def send_event():
    """ Sends events to EventQueue based on table 'maintenance' """
    for event in events:
        emotdid = event['emotdid']
        mid = event['maintenanceid']
        type = event['type']

        # handle that follow-ups copies manitenance units from its parent
        sql = """SELECT key, value, type
                 FROM emotd_related
                 INNER JOIN emotd USING (emotdid)
                 WHERE emotdid=%s
                 AND emotdid NOT IN (SELECT replaces_emotd
                                     FROM emotd
                                     WHERE replaces_emotd IS NOT NULL)"""
        database.execute(sql, (emotdid, ))
        
        for (key,val,emotdtype) in database.fetchall():
            target = 'eventEngine'
            subsystem = 'emotd'
            severity = 50
            source = subsystem #'maintenance'
            eventtype = 'maintenanceState'
            state = 'e'
            value = 0
            if type == 'active':
                if emotdtype=='info':
                    severity = 10
                elif emotdtype=='internal':
                    severity = 20
                elif emotdtype=='scheduled':
                    severity = 60
                elif emotdtype=='error':
                    severity = 80
                state = 's'
                value = 100

            # type-dependant handling

            # type netbox
            if key=='netbox':

                #get new eventqid to insert into eventq AND eventqvar
                database.execute("select nextval('eventq_eventqid_seq')")
                eventqid = database.fetchone()[0]

                #select info from the netbox
                database.execute("select deviceid,sysname from netbox where netboxid = %d" % int(val))
                result = database.fetchone()
                if result:
                    (deviceid,sysname) = result

                    #insert into eventq
                    database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,deviceid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(val), int(deviceid), source, severity, state, value))

                    #insert sysname into eventqvar
                    database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, sysname))

                    # Append to list of boxes taken off maintenance
                    # during this run
                    boxesOffMaintenance.append(int(val))

            # type room or location
            elif key=='room' or key=='location':
                if key=='room':
                    #get all netboxes from this room
                    database.execute("select netboxid, sysname, deviceid from netbox where roomid=%s",(val,))
                else:
                    #get all netboxes from this location
                    database.execute("select netboxid, sysname, deviceid from netbox inner join room using (roomid) where locationid=%s",(val,))

                #for each netbox
                for (netboxid, sysname, deviceid) in database.fetchall():

                    #get eventqid
                    database.execute("select nextval('eventq_eventqid_seq')")
                    eventqid = database.fetchone()[0]

                    #insert into eventq
                    database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,deviceid,source,severity,state,value) values (%d,'%s','%s','%s','%s','%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(netboxid), int(deviceid), source, severity, state, value))

                    #insert sysname into eventqvar
                    database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), 'netbox', sysname))

                    # Append to list of boxes taken off maintenance
                    # during this run
                    boxesOffMaintenance.append(int(netboxid))

            #type module
            elif key=='module':

                #get eventqid
                database.execute("select nextval('eventq_eventqid_seq')")
                eventqid = database.fetchone()[0]

                #select useful information regarding this module
                database.execute("select netboxid, deviceid, module, descr from module where moduleid=%d" % int(val))
                result = database.fetchone()
                if result:
                    (netboxid, deviceid, module, descr) = result

                    #insert into eventq
                    database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,deviceid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(netboxid), int(deviceid), source, severity, state, value))

                    #insert into eventqvar
                    database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, str(module) + ":" + descr))

            #type service
            elif key=='service':

                #get eventqid
                database.execute("select nextval('eventq_eventqid_seq')")
                eventqid = database.fetchone()[0]

                #select useful information regarding the service
                database.execute("select netboxid, handler from service where serviceid=%d" % int(val))
                result = database.fetchone()
                if result:
                    (netboxid, handler) = result

                    #insert into eventq
                    database.execute("insert into eventq (eventqid,target,eventtypeid,netboxid,subid,source,severity,state,value) values (%d,'%s','%s',%d,%d,'%s',%d,'%s',%d)" % (int(eventqid), target, eventtype, int(netboxid), int(val), source, severity, state, value))

                    #insert into eventqvar
                    database.execute("insert into eventqvar (eventqid,var,val) values (%d, '%s', '%s')" % (int(eventqid), key, handler))
            else:

                #never happens
                raise repr("Unrecognised equipment key")

        #update maintenance states
        database.execute("update maintenance set state='%s' where maintenanceid = %d" % (type, int(mid)))

        #commit transaction
        connection.commit()

def remove_forgotten():
    """Remove 'forgotten' netboxes from their maintenance state.

    Sometimes, like when netboxes have been deleted from a message
    during its active maintenance window, we will no longer know that
    the box has gone on maintenenance and should be taken off.  This
    function takes all 'forgotten' netboxes off maintenance.
    """
    # This SQL retrieves a list of boxes that are supposed to be on
    # maintenance, according to the schedule.
    sched = """SELECT n.netboxid, n.deviceid, n.sysname
               FROM maintenance_view mv
               INNER JOIN netbox n ON (n.netboxid = mv.value)
               WHERE mv.key='netbox'
                 AND mv.state='active'

               UNION

               SELECT n.netboxid, n.deviceid, n.sysname
               FROM maintenance_view mv
               INNER JOIN netbox n ON (n.roomid = mv.value)
               WHERE mv.key='room'
                 AND mv.state='active'

               UNION

               SELECT n.netboxid, n.deviceid, n.sysname
               FROM maintenance_view mv
               INNER JOIN netbox n ON (n.roomid IN
                                       (SELECT roomid
                                        FROM room
                                        WHERE locationid = mv.value))
               WHERE mv.key='room'
                 AND mv.state='active'"""

    # This SQL retrieves a list of boxes that are currently on
    # maintenance, according to the alert history.
    actual = """SELECT n.netboxid, n.deviceid, n.sysname
                FROM alerthist a
                LEFT JOIN netbox n USING (netboxid)
                WHERE eventtypeid='maintenanceState'
                  AND netboxid IS NOT NULL
                  AND end_time = 'infinity'"""

    # The full SQL is a set operation to select all boxes that are
    # currently on maintenance and subtracts those that are supposed
    # to be on maintenance - resulting in a list of boxes that should
    # be taken off maintenance immediately.
    fullSQL = "(%s) \n EXCEPT \n (%s)" % (actual, sched)
    database.execute(fullSQL);

    target = 'eventEngine'
    source = 'emotd'
    severity = 50
    eventtype = 'maintenanceState'
    state = 'e'
    value = 0
    for (netboxid, deviceid, sysname) in database.fetchall():
        if int(netboxid) in boxesOffMaintenance:
            # MaintenenceOff-events posted during this run might not
            # have been processed by eventEngine yet. We discard these
            # boxes here.
            continue
        print >> sys.stderr, ("Box %s (%d) was on unscheduled " +
                              "maintenance, taking off maintenance now...") % \
                              (sysname, netboxid)
        #get eventqid
        database.execute("select nextval('eventq_eventqid_seq')")
        eventqid = database.fetchone()[0]

        #insert into eventq
        database.execute("""INSERT INTO eventq
                            (eventqid, target, eventtypeid, netboxid,
                             deviceid,source,severity,state,value)
                            VALUES (%d,%s,%s,%s,%s,%s,%d,%s,%d)""",
                         (int(eventqid), target, eventtype, int(netboxid),
                          int(deviceid), source, severity, state, value))

        #insert sysname into eventqvar
        database.execute("""INSERT INTO eventqvar
                            (eventqid, var, val)
                            VALUES (%d, %s, %s)""",
                         (int(eventqid), 'netbox', sysname))
    connection.commit()

if __name__ == '__main__':
    schedule()
    check_state()
    send_event()
    remove_forgotten()
