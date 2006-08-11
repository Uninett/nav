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

def getTasks(where = False):
    """
    Get maintenance tasks

    Input:
        where   Where clause of query

    Returns:
        If tasks found, returns dictionary with results
        If no tasks found, returns false

    """

    select = "SELECT maint_taskid, maint_start, maint_end, description, author, state FROM maint_task"
    order = "maint_start DESC"

    if where:
        sql = "%s WHERE %s ORDER BY %s" % (select, where, order)
    else:
        sql = "%s ORDER BY %s" % (select, order)

    # FIXME: Log query
    db.execute(sql)
    if not db.rowcount:
        return False
    result = db.dictfetchall()
    # FIXME: Log result

    return result

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
        'maint_start': maint_start,
        'maint_end': maint_end,
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
