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
FIXME
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id:$"

from mod_python import apache

import nav.db
from nav.web.URI import URI
from nav.web.templates.Messages2ListTemplate import Messages2ListTemplate
from nav.web.templates.Messages2NewTemplate import Messages2NewTemplate

dbconn = nav.db.getConnection('webfront', 'manage')
db = dbconn.cursor()

def handler(req):
    """Handler for the Messages 2 subsystem."""

    # Get arguments
    args = URI(req.unparsed_uri)

    # Get section
    if len(args.path.split('/')[-1]):
        section = args.path.split('/')[-1]
    else:
        section = 'all'

    # Create section page
    if section == 'active':
        page = Messages2ListTemplate()
        page.title = 'Active messages'
        page.msgs = msgsquery(['publish_start < now()', 'publish_end > now()'])
    elif section == 'planned':
        page = Messages2ListTemplate()
        page.title = 'Planned messages'
        page.msgs = msgsquery(['publish_start > now()'])
    elif section == 'historic':
        page = Messages2ListTemplate()
        page.title = 'Historic messages'
        page.msgs = msgsquery(['publish_end < now()'])
    elif section == 'new':
        page = Messages2NewTemplate() # FIXME: Create template
        page.title = 'New message'
    else:
        page = Messages2ListTemplate()
        page.title = 'All messages'
        page.msgs = msgsquery()

    # Create menu
    page.menu = [{'link': 'all', 'text': 'All', 'admin': False},
                {'link': 'active', 'text': 'Active', 'admin': False},
                {'link': 'planned', 'text': 'Planned', 'admin': False},
                {'link': 'historic', 'text': 'Historic', 'admin': False},
                {'link': 'new', 'text': 'Create new', 'admin': True}]
    page.current = section
  
    # Done, output the page
    req.content_type = 'text/html'
    req.send_http_header()
    req.write(page.respond())
    return apache.OK

def msgsquery(where = []):
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

