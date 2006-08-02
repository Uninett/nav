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
Common methods for message management
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

def getMsgs(where = []):
    select = "SELECT messageid, title, description, tech_description, publish_start, publish_end, author, last_changed, replaces_message FROM message"
    where = " AND ".join(where)
    order = "publish_start DESC"

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

def setMsg(title, description, tech_description, publish_start,
 publish_end, author, replaces_message):
    sql = """INSERT INTO message (
            title,
            description,
            tech_description,
            publish_start,
            publish_end,
            author,
            replaces_message
        ) VALUES (
            %(title)s,
            %(description)s,
            %(tech_description)s,
            %(publish_start)s,
            %(publish_end)s,
            %(author)s,
            %(replaces_message)s
        )"""

    data = {
        'title': title,
        'description': description,
        'tech_description': tech_description or None,
        'publish_start': time.strftime('%Y-%m-%d %H:%M:%S', publish_start),
        'publish_end': time.strftime('%Y-%m-%d %H:%M:%S', publish_end),
        'author': author,
        'replaces_message': replaces_message or None
    }

    if apache:
        apache.log_error("Messages2 query: " + sql % data, apache.APLOG_NOTICE)

    db.execute(sql, data)
    db.execute("SELECT CURRVAL('message_messageid_seq')")
    id = db.dictfetchone()['currval']

    if id and apache:
        apache.log_error("Messages2 query returned ID %d." % id,
         apache.APLOG_NOTICE)

    return id

def getMsgTasks(where = []):
    select = "SELECT ..." # FIXME
