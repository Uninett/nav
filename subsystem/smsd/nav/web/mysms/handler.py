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
My SMS status page

The 'My SMS' status page lists all messages for the current users in the
given number of past days.
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id: mysms.py 3464 2006-06-22 08:58:05Z jodal $"

from mod_python import apache

import nav.db
from nav.web.URI import URI
from nav.web.templates.MySMSTemplate import MySMSTemplate

dbconn = nav.db.getConnection('webfront', 'navprofile')
db = dbconn.cursor()

def handler(req):
    """Handler for the My SMS status page."""

    args = URI(req.unparsed_uri)

    # Setup template
    page = MySMSTemplate()
    req.content_type = 'text/html'
    req.send_http_header()

    # Get number of days to search backwards
    days = 7
    if args.get('days') and args.get('days').isdigit():
        days = int(args.get('days'))
    if days > 99999: # Back to the 18th century should be enough
        days = 99999
    page.days = days

    # Get phone number of user
    phones = None
    for phone in phonesdbquery(req.session['user']):
        if phones:
            phones = "%s, %s" % (phones, phone[0])
        else:
            phones = phone[0]
    page.phones = phones

    # Pass messages to the template
    if phones:
        page.messages = smsdbquery(phones, days)
    else:
        page.messages = None
    
    req.write(page.respond())
    return apache.OK


def phonesdbquery(userid):
    """Get phone numbers from database given user id."""

    smstype = 2

    if str(userid).isdigit():
        userid = int(str(userid))
    else:
        return False

    select = "SELECT adresse FROM alarmadresse"

    where = []
    where.append("accountid = '%d'" % userid)
    where.append("type = '%d'" % smstype)
    where = " AND ".join(where)

    sql = "%s WHERE %s" % (select, where)

    if apache:
        apache.log_error("My SMS query: " + sql, apache.APLOG_NOTICE)

    db.execute(sql)
    result = db.fetchall()

    if result and apache:
        apache.log_error("My SMS query returned %d results." %
         len(result), apache.APLOG_NOTICE)

    return result


def smsdbquery(phones, days = 7, orderby = ''):
    """Get messages from database given phone numbers and number of days."""

    select = "SELECT time, timesent, phone, severity, msg, sent FROM smsq"

    where = []
    where.append("time > now() - INTERVAL '%s day'" % days)
    where.append("phone IN (%s)" % phones)
    where = " AND ".join(where)

    if not orderby:
        orderby = 'time DESC, severity DESC'

    sql = "%s WHERE %s ORDER BY %s" % (select, where, orderby)

    if apache:
        apache.log_error("My SMS query: " + sql, apache.APLOG_NOTICE)

    db.execute(sql)
    result = db.dictfetchall()

    if result and apache:
        apache.log_error("My SMS query returned %d results." %
         len(result), apache.APLOG_NOTICE)

    return result

