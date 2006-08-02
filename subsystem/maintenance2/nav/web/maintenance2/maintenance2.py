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

def getTasks(where = []):
    select = "SELECT maint_taskid, maint_start, maint_end, description, author, state FROM maint_task"
    where = " AND ".join(where)
    order = "maint_start DESC"

    if len(where):
        sql = "%s WHERE %s ORDER BY %s" % (select, where, order)
    else:
        sql = "%s ORDER BY %s" % (select, order)

    if apache:
        apache.log_error("Messages2 query: " + sql, apache.APLOG_NOTICE)

    db.execute(sql)
    result = db.dictfetchall()

    if result and apache:
        apache.log_error("Messages2 query returned %d results." % 
         len(result), apache.APLOG_NOTICE)

    return result

def setTask(maint_start, maint_end, description, author, state):
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
        'maint_start': maint_start,
        'maint_end': maint_end,
        'description': description,
        'author': author,
        'state': state
    }

    if apache:
        apache.log_error("Messages2 query: " + sql % date, apache.APLOG_NOTICE)
    
    db.execute(sql, data)
    db.execute("SELECT CURRVAL('maint_task_maint_taskid_seq')")
    id = db.dictfetchone()['currval']

    if id and apache:
        apache.log_error("Messages2 query returned ID %d." % id,
         apache.APLOG_NOTICE)

    return id
