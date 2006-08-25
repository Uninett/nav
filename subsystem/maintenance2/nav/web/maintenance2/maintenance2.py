#! /usr/bin/env python
# -*- coding: ISO8859-1 -*-
#
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
# Author: Stein Magnus Jodal <stein.magnus@jodal.no>
#

"""
Common methods for maintenance management
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id:$"

import time
from mod_python import apache, util
import nav.db

dbconn = nav.db.getConnection('webfront', 'manage')
db = dbconn.cursor()

def getTasks(where = False, order = 'maint_end DESC'):
    """
    Get maintenance tasks

    Input:
        where   Where clause of query

    Returns:
        If tasks found, returns dictionary with results
        If no tasks found, returns false

    """

    select = """SELECT maint_taskid, maint_start, maint_end,
        maint_end - maint_start AS interval,
        description, author, state
        FROM maint_task"""

    if where:
        sql = "%s WHERE %s ORDER BY %s" % (select, where, order)
    else:
        sql = "%s ORDER BY %s" % (select, order)

    # FIXME: Log query
    db.execute(sql)
    if not db.rowcount:
        return False
    results = db.dictfetchall()
    # FIXME: Log result

    # Attach components belonging to this message
    for i, result in enumerate(results):
        results[i]['components'] = getComponents(results[i]['maint_taskid']) \
            or None

    return results

def setTask(taskid, maint_start, maint_end, description, author, state):
    """
    Insert or update a maintenance task

    Input:
        taskid      Maintenance task ID if update, set to false if new task
        maint_start Start time of task
        maint_end   End time of task
        description Description of the task
        author      Username of author
        state       State of task, initally 'scheduled', used by other
                    subsystems

    Returns:
        msgid       ID of updated or inserted task

    """

    if taskid:
        sql = """UPDATE maint_task SET
                maint_start = %(maint_start)s,
                maint_end = %(maint_end)s,
                description = %(description)s,
                author = %(author)s,
                state = %(state)s
            WHERE
                maint_taskid = %(maint_taskid)d"""
    else:
        sql = """INSERT INTO maint_task (
                maint_start,
                maint_end,
                description,
                author,
                state
            ) VALUES (
                %(maint_start)s,
                %(maint_end)s,
                %(description)s,
                %(author)s,
                %(state)s
            )"""

    data = {
        'maint_taskid': taskid,
        'maint_start': time.strftime('%Y-%m-%d %H:%M:%S', maint_start),
        'maint_end': time.strftime('%Y-%m-%d %H:%M:%S', maint_end),
        'description': description,
        'author': author,
        'state': state
    }

    # FIXME: Log query
    db.execute(sql, data)
    if not taskid:
        db.execute("SELECT CURRVAL('maint_task_maint_taskid_seq')")
        taskid = db.dictfetchone()['currval']
    # FIXME: Log result

    return taskid

def getComponents(taskid):
    """
    Get maintenance components belonging to a maintenance task

    Input:
        taskid  ID of maintenance task

    Returns:
        If components found, returns dictionary with results
        If no compononets found, returns false

    """

    sql = """SELECT key, value
        FROM maint_component
        WHERE maint_taskid = %(maint_taskid)d
        ORDER BY key, value"""
    data = {'maint_taskid': taskid}

    # FIXME: Log query
    db.execute(sql, data)
    if not db.rowcount:
        return False
    results = db.dictfetchall()
    # FIXME: Log result

    # Attach netboxes belonging to this component
    for i, result in enumerate(results):
        if results[i]['key'] == 'location':
            results[i]['extra'] = getLocation(results[i]['value']) or None
        if results[i]['key'] == 'room':
            results[i]['extra'] = getRoom(results[i]['value']) or None
        if results[i]['key'] == 'netbox':
            results[i]['extra'] = getNetbox(results[i]['value']) or None
        if results[i]['key'] == 'service':
            results[i]['extra'] = getService(results[i]['value']) or None

    sortedresults = []
    for i, result in enumerate(results):
        if results[i]['key'] == 'location':
            sortedresults.append(results[i])
    for i, result in enumerate(results):
        if results[i]['key'] == 'room':
            sortedresults.append(results[i])
    for i, result in enumerate(results):
        if results[i]['key'] == 'netbox':
            sortedresults.append(results[i])
    for i, result in enumerate(results):
        if results[i]['key'] == 'service':
            sortedresults.append(results[i])

    return sortedresults

def getLocation(locationid):
    """
    Get location (part of maintenance component)

    Input:
        locationid    ID of location

    Returns:
        If location found, returns dictionary with results
        If no location found, returns false

    """

    sql = """SELECT l.locationid, l.descr AS locationdescr
        FROM location l
        WHERE locationid = %(locationid)s"""
    data = {'locationid': locationid}

    # FIXME: Log query
    db.execute(sql, data)
    if not db.rowcount:
        return False
    result = db.dictfetchall()
    # FIXME: Log result
    return result[0]

def getRoom(roomid):
    """
    Get room (part of maintenance component)

    Input:
        roomid    ID of room

    Returns:
        If room found, returns dictionary with results
        If no room found, returns false

    """

    sql = """SELECT
            r.roomid, r.descr AS roomdescr,
            l.locationid, l.descr AS locationdescr
        FROM room r JOIN location l ON (r.locationid = l.locationid)
        WHERE roomid = %(roomid)s"""
    data = {'roomid': roomid}

    # FIXME: Log query
    db.execute(sql, data)
    if not db.rowcount:
        return False
    result = db.dictfetchall()
    # FIXME: Log result
    return result[0]


def getNetbox(netboxid):
    """
    Get netbox (part of maintenance component)

    Input:
        netboxid    ID of netbox

    Returns:
        If netbox found, returns dictionary with results
        If no netbox found, returns false

    """

    sql = """SELECT
            n.netboxid, n.sysname, n.ip,
            r.roomid, r.descr AS roomdescr,
            l.locationid, l.descr AS locationdescr
        FROM netbox n NATURAL JOIN room r
            JOIN location l ON (r.locationid = l.locationid)
        WHERE netboxid = %(netboxid)d"""
    data = {'netboxid': int(netboxid)}

    # FIXME: Log query
    db.execute(sql, data)
    if not db.rowcount:
        return False
    result = db.dictfetchall()
    # FIXME: Log result
    return result[0]

def getService(serviceid):
    """
    Get service (part of maintenance component)

    Input:
        serviceid   ID of service

    Returns:
        If service found, returns dictionary with results
        If no service found, returns false

    """
    
    sql = """SELECT
            s.serviceid, s.handler,
            n.netboxid, n.sysname, n.ip,
            r.roomid, r.descr AS roomdescr,
            l.locationid, l.descr AS locationdescr
        FROM service s NATURAL JOIN netbox n NATURAL JOIN room r
            JOIN location l ON (r.locationid = l.locationid)
        WHERE s.serviceid = %(serviceid)d"""
    data = {'serviceid': int(serviceid)}

    # FIXME: Log query
    db.execute(sql, data)
    if not db.rowcount:
        return False
    result = db.dictfetchall()
    # FIXME: Log result
    return result[0]
