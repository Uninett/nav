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
Common methods for message management
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id:$"

import logging
import time
import psycopg2.extras
import nav.db

logger = logging.getLogger('nav.messages')

def getMsgs(where = False, order = 'publish_start DESC'):
    """
    Get messages with connected tasks

    Input:
        where   Where clause for the query. Do NOT use user supplied data in
                the where clause without proper sanitation.
        order   Result order

    Returns:
        If messages found, returns dictionary with results
        If no messages found, returns false

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    select = """SELECT
        messageid, title, description, tech_description,
        publish_start, publish_end, author, last_changed,
        replaces_message, replaces_message_title, replaces_message_description,
        replaces_message_tech_description, replaces_message_publish_start,
        replaces_message_publish_end, replaces_message_author,
        replaces_message_last_changed,
        replaced_by, replaced_by_title, replaced_by_description,
        replaced_by_tech_description, replaced_by_publish_start,
        replaced_by_publish_end, replaced_by_author,
        replaced_by_last_changed
        FROM message_with_replaced"""

    if where:
        sql = "%s WHERE %s ORDER BY %s" % (select, where, order)
    else:
        sql = "%s ORDER BY %s" % (select, order)

    logger.debug("getMsgs() query: %s", sql)
    db.execute(sql)
    logger.debug("getMsgs() number of results: %d", db.rowcount)
    if not db.rowcount:
        return []
    results = db.fetchall()

    # Attach tasks connected to this message
    for i, result in enumerate(results):
        results[i]['tasks'] = getMsgTasks(results[i]['messageid']) or None

    return results

def getMsg(msgid):
    """
    Get one message with connected tasks

    getMsgs() wrapper which ensures sanitation of the where argument.

    Input:
        msgid               Message ID

    Returns:
        If message found, return dictionary with results
        If no message found, returns false

    """

    where = 'messageid = %d' % int(msgid)
    return getMsgs(where)

def setMsg(msgid, title, description, tech_description, publish_start,
    publish_end, author, replaces_message):
    """
    Insert or update a message

    Input:
        msgid               Message ID if update, set to false if new message
        title               Message title
        description         The message itself
        tech_description    A more detailed technical description
        publish_start       Time to publish message
        publish_end         Time to expire message
        author              Username of author
        replaces_message    Message ID of old message replaced by this one

    Returns:
        msgid               ID of updated or inserted message
    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    if msgid:
        sql = """UPDATE message SET
                title = %(title)s,
                description = %(description)s,
                tech_description = %(tech_description)s,
                publish_start = %(publish_start)s,
                publish_end = %(publish_end)s,
                author = %(author)s,
                last_changed = now(),
                replaces_message = %(replaces_message)d
            WHERE
                messageid = %(messageid)d"""
    else:
        sql = """INSERT INTO message (
                title, description, tech_description, publish_start,
                publish_end, author, replaces_message
            ) VALUES (
                %(title)s, %(description)s, %(tech_description)s,
                %(publish_start)s, %(publish_end)s, %(author)s,
                %(replaces_message)d
            )"""

    data = {
        'messageid': msgid or None,
        'title': title,
        'description': description,
        'tech_description': tech_description or None,
        'publish_start': time.strftime('%Y-%m-%d %H:%M:%S', publish_start),
        'publish_end': time.strftime('%Y-%m-%d %H:%M:%S', publish_end),
        'author': author,
        'replaces_message': replaces_message or None
    }

    logger.debug("setMsg() query: %s, data: %s", (sql, data))
    db.execute(sql, data)
    if not msgid:
        db.execute("SELECT CURRVAL('message_messageid_seq')")
        msgid = db.fetchone()['currval']
    logger.debug("setMsg() number of results: %d", db.rowcount)

    return msgid

def getMsgTasks(msgid):
    """
    Get tasks connected to a message

    Input:
        msgid   Message ID of message

    Returns:
        If messages found, returns dictionary with results
        If no messages found, returns false

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    sql = """SELECT maint_taskid, maint_start, maint_end, description,
        author, state
        FROM maint_task NATURAL JOIN message_to_maint_task
        WHERE messageid = %(messageid)s
        ORDER BY maint_start, description"""
    data = {'messageid': msgid}

    logger.debug("getMsgTasks() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("getMsgTasks() number of results: %d", db.rowcount)
    if not db.rowcount:
        return False
    result = db.fetchall()
    return result

def setMsgTask(msgid, taskid):
    """
    Create connection between message and maintenance task

    Input:
        msgid   Message ID
        taskid  Maintenance task ID

    Returns:
        If connection already exists, returns False
        If connection was created, reeturns True

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor()

    data = {'messageid': msgid, 'maint_taskid': taskid}

    # Check if message and task is already linked
    sql = """SELECT messageid, maint_taskid
        FROM message_to_maint_task
        WHERE messageid = %(messageid)d AND maint_taskid = %(maint_taskid)d"""
    logger.debug("setMsgTask() #1 query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("setMsgTask() #1 number of results: %d", db.rowcount)

    if db.rowcount:
        return False
    else:
        sql = """INSERT INTO message_to_maint_task (
                messageid, maint_taskid
            ) VALUES (
                %(messageid)d, %(maint_taskid)d
            )"""

        logger.debug("setMsgTask() #2 query: %s", sql % data)
        db.execute(sql, data)
        logger.debug("setMsgTask() #2 number of results: %d", db.rowcount)
        return True

def removeMsgTasks(msgid):
    """
    Remove connection between given message and all tasks

    Input:
        msgid   Message ID

    Returns:
        If connections removed, returns True
        If no connections removed, returns False

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor()

    data = {'messageid': msgid}
    sql = "DELETE FROM message_to_maint_task WHERE messageid = %(messageid)d"

    logger.debug("removeMsgTasks() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("removeMsgTasks() number of results: %d", db.rowcount)

    if db.rowcount:
        return True
    else:
        return False

def expireMsg(msgid):
    """
    Expire a message by setting publish_end to current time

    Input:
        msgid   ID of message to be expired

    Returns:
        Always returns true, unless some error occurs.

    """

    dbconn = nav.db.getConnection('webfront', 'manage')
    db = dbconn.cursor()

    sql = """UPDATE message SET publish_end = now()
        WHERE messageid = %(messageid)d"""

    data = {'messageid': msgid}

    logger.debug("expireMsg() query: %s", sql % data)
    db.execute(sql, data)
    logger.debug("expireMsg() number of results: %d", db.rowcount)

    return True
