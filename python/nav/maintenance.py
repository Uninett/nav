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
# Author: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

"""
Common methods for maintenance management
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id:$"

import logging
import time
import psycopg2.extras

import nav.db

logger = logging.getLogger('nav.maintenance')

def getTasks(where = False, order = 'maint_end DESC'):
    """
    Get maintenance tasks

    Input:
        where   Where clause of query. Do NOT use user supplied data in the
                where clause without proper sanitation.

    Returns:
        If tasks found, returns dictionary with results
        If no tasks found, returns false

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    select = """SELECT maint_taskid, maint_start, maint_end,
        maint_end - maint_start AS interval,
        description, author, state
        FROM maint_task"""

    if where:
        sql = "%s WHERE %s ORDER BY %s" % (select, where, order)
    else:
        sql = "%s ORDER BY %s" % (select, order)

    logger.debug("getTask() query: %s", sql)
    db.execute(sql)
    logger.debug("getTask() number of results: %d", db.rowcount)
    if not db.rowcount:
        return False
    results = [dict(row) for row in db.fetchall()]

    # Attach components belonging to this message
    for i, result in enumerate(results):
        results[i]['components'] = getComponents(results[i]['maint_taskid']) \
            or []

    return results

def getTask(taskid):
    """
    Get one maintenance task

    getTasks() wrapper which ensures sanitation of the where argument.

    Input:
        taskid      Maintenance task ID

    Returns:
        If task found, returns dictionary with results
        If no task found, returns false

    """

    where = 'maint_taskid = %d' % int(taskid)
    return getTasks(where)

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

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if taskid:
        sql = """UPDATE maint_task SET
                maint_start = %(maint_start)s,
                maint_end = %(maint_end)s,
                description = %(description)s,
                author = %(author)s,
                state = %(state)s
            WHERE
                maint_taskid = %(maint_taskid)s"""
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

    if not isinstance(description, unicode):
        description = description.decode('utf-8')

    data = {
        'maint_taskid': taskid,
        'maint_start': time.strftime('%Y-%m-%d %H:%M:%S', maint_start),
        'maint_end': time.strftime('%Y-%m-%d %H:%M:%S', maint_end),
        'description': description,
        'author': author,
        'state': state
    }

    logger.debug("setTask() query: %s", sql % data)
    db.execute(sql, data)
    if not taskid:
        db.execute("SELECT CURRVAL('maint_task_maint_taskid_seq')")
        taskid = db.fetchone()['currval']
    logger.debug("setTask() number of results: %d", db.rowcount)

    return taskid

def getComponents(taskid):
    """
    Get maintenance components belonging to a maintenance task

    Input:
        taskid  ID of maintenance task

    Returns:
        If components found, returns dictionary with results
        If no components found, returns false

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = """SELECT key, value
        FROM maint_component
        WHERE maint_taskid = %(maint_taskid)s
        ORDER BY key, value"""
    data = {'maint_taskid': taskid}

    logger.debug("getComponents() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("getComponents() number of results: %d", db.rowcount)
    if not db.rowcount:
        return False
    results = [dict(row) for row in db.fetchall()]

    # Attach information about the components
    for i, result in enumerate(results):
        results[i]['info'] = getComponentInfo(results[i]['key'],
                                              results[i]['value']) or None

    # Sort components
    results = sortComponents(results)

    return results

def setComponents(taskid, components):
    """
    Remove all components connected to a task and add this new set of
    components instead.

    Input:
        taskid      ID of maintenance task
        components  List of component key/value pairs

    Returns:
        If function completes, returns True

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor()

    # Remove old components
    sql = """DELETE FROM maint_component
        WHERE maint_taskid = %(maint_taskid)s"""
    data = { 'maint_taskid': taskid }
    logger.debug("setComponents() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("setComponents() number of results: %d", db.rowcount)

    # Insert new components
    sql = """INSERT INTO maint_component (
            maint_taskid,
            key,
            value
        ) VALUES (
            %(maint_taskid)s,
            %(key)s,
            %(value)s
        )"""

    for component in components:
        data = {
            'maint_taskid': taskid,
            'key': component['key'],
            'value': component['value']
        }

        logger.debug("setComponents() query: %s", sql % data)
        db.execute(sql, data)
        logger.debug("setComponents() number of results: %d", db.rowcount)

    return True

def sortComponents(components):
    """
    Sort components in the following order:
    location, room, netbox, service

    Input:
        components  List of components to be sorted

    Returns:
        A sorted list of the components

    """

    results = []

    for i, component in enumerate(components):
        if components[i]['key'] == 'location':
            results.append(components[i])

    for i, component in enumerate(components):
        if components[i]['key'] == 'room':
            results.append(components[i])

    for i, component in enumerate(components):
        if components[i]['key'] == 'netbox':
            results.append(components[i])

    for i, component in enumerate(components):
        if components[i]['key'] == 'service':
            results.append(components[i])

    return results

def getComponentInfo(key, value):
    """
    Get information about component

    Input:
        key     Type of component
        value   Componenent ID

    Returns:
        If component found, returns dictionary with results
        If no component found, returns false

    """

    if key == 'location':
        return getLocation(value)
    if key == 'room':
        return getRoom(value)
    if key == 'netbox':
        return getNetbox(value)
    if key == 'service':
        return getService(value)

def getLocation(locationid):
    """
    Get location (part of maintenance component)

    Input:
        locationid    ID of location

    Returns:
        If location found, returns dictionary with results
        If no location found, returns false

    """

    if not len(locationid):
        return False

    if hasattr(locationid, 'value'):
        locationid = locationid.value

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = """SELECT l.locationid, l.descr AS locationdescr
        FROM location l
        WHERE locationid = %(locationid)s"""
    data = {'locationid': locationid}

    logger.debug("getLocation() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("getLocation() number of results: %d", db.rowcount)
    if not db.rowcount:
        return False
    result = db.fetchall()

    return dict(result[0])

def getRoom(roomid):
    """
    Get room (part of maintenance component)

    Input:
        roomid    ID of room

    Returns:
        If room found, returns dictionary with results
        If no room found, returns false

    """

    if not len(roomid):
        return False

    if hasattr(roomid, 'value'):
        roomid = roomid.value

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = """SELECT
            r.roomid, r.descr AS roomdescr,
            l.locationid, l.descr AS locationdescr
        FROM room r
            JOIN location l ON (r.locationid = l.locationid)
        WHERE roomid = %(roomid)s"""
    data = {'roomid': roomid}

    logger.debug("getRoom() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("getRoom() number of results: %d", db.rowcount)
    if not db.rowcount:
        return False
    result = db.fetchall()

    return dict(result[0])

def getNetbox(netboxid):
    """
    Get netbox (part of maintenance component)

    Input:
        netboxid    ID of netbox

    Returns:
        If netbox found, returns dictionary with results
        If no netbox found, returns false

    """

    if not len(netboxid):
        return False

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = """SELECT
            n.netboxid, n.sysname, n.ip,
            r.roomid, r.descr AS roomdescr,
            l.locationid, l.descr AS locationdescr
        FROM netbox n
            JOIN room r ON (n.roomid = r.roomid)
            JOIN location l ON (r.locationid = l.locationid)
        WHERE netboxid = %(netboxid)s"""
    data = {'netboxid': int(netboxid)}

    logger.debug("getNetbox() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("getNetbox() number of results: %d", db.rowcount)
    if not db.rowcount:
        return False
    result = db.fetchall()

    return dict(result[0])

def getService(serviceid):
    """
    Get service (part of maintenance component)

    Input:
        serviceid   ID of service

    Returns:
        If service found, returns dictionary with results
        If no service found, returns false

    """

    if not len(serviceid):
        return False

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = """SELECT
            s.serviceid, s.handler,
            n.netboxid, n.sysname, n.ip,
            r.roomid, r.descr AS roomdescr,
            l.locationid, l.descr AS locationdescr
        FROM service s
            JOIN netbox n ON (s.netboxid = n.netboxid)
            JOIN room r ON (n.roomid = r.roomid)
            JOIN location l ON (r.locationid = l.locationid)
        WHERE s.serviceid = %(serviceid)s"""
    data = {'serviceid': int(serviceid)}

    logger.debug("getService() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("getService() number of results: %d", db.rowcount)
    if not db.rowcount:
        return False
    result = db.fetchall()

    return dict(result[0])

def cancelTask(taskid):
    """
    Cancel a maintenance task by setting state to 'canceled'

    Input:
        msgid   ID of maintenance task to be canceled

    Returns:
        Always returns true, unless some error occurs.

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor()

    sql = """UPDATE maint_task SET state = 'canceled'
        WHERE maint_taskid = %(maint_taskid)s"""

    data = {'maint_taskid': taskid}

    logger.debug("cancelTask() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("cancelTask() number of results: %d", db.rowcount)

    return True
