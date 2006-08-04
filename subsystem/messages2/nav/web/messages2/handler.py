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

import time
from mod_python import apache, util

import nav.db
from nav.web.URI import URI
from nav.web.templates.Messages2ListTemplate import Messages2ListTemplate
from nav.web.templates.Messages2NewTemplate import Messages2NewTemplate
from nav.web.messages2 import messages2
from nav.web.maintenance2 import maintenance2

dbconn = nav.db.getConnection('webfront', 'manage')
db = dbconn.cursor()

def handler(req):
    """Handler for the Messages 2 subsystem."""

    # Initialize form
    keep_blank_values = True
    req.form = util.FieldStorage(req, keep_blank_values)

    # Get arguments
    args = URI(req.unparsed_uri)

    # Get section
    if len(args.path.split('/')[-1]):
        section = args.path.split('/')[-1]
    else:
        section = 'active'
    
    # Create section page
    if section == 'planned':
        page = Messages2ListTemplate()
        page.title = 'Planned Messages'
        page.msgs = messages2.getMsgs(['publish_start > now()'])
    elif section == 'historic':
        page = Messages2ListTemplate()
        page.title = 'Historic Messages'
        page.msgs = messages2.getMsgs(['publish_end < now()'])
    elif section == 'view' and args.get('id').isdigit():
        page = Messages2ListTemplate()
        page.title = 'Message'
        viewid = int(args.get('id'))
        page.msgs = messages2.getMsgs(['messageid = %d' % viewid])
    elif section == 'new':
        page = Messages2NewTemplate()
        page.title = 'Create New Message'
        page.tasks = maintenance2.getTasks(['maint_end > now()'])
        page.submit = req.form.has_key('new-do')
        if page.submit:
            page.errors = []
            if req.form.has_key('title') and req.form['title']:
                title = req.form['title']
                page.formtitle = title
            else:
                page.errors.append('You did not supply a title.')

            if req.form.has_key('description') and req.form['description']:
                description = req.form['description']
                page.description = description
            else:
                page.errors.append('You did not supply a description.')

            if req.form.has_key('tech_description') and len(req.form['tech_description']) > 0:
                tech_description = req.form['tech_description']
                page.tech_description = tech_description
            else:
                tech_description = False

            if (req.form.has_key('start_year') and req.form['start_year']
                and req.form.has_key('start_month') and req.form['start_month']
                and req.form.has_key('start_day') and req.form['start_day']
                and req.form.has_key('start_hour') and req.form['start_hour']
                and req.form.has_key('start_min') and req.form['start_min']):
                publish_start = '%4d-%02d-%02d %02d:%02d' % (
                 int(req.form['start_year']), int(req.form['start_month']),
                 int(req.form['start_day']), int(req.form['start_hour']),
                 int(req.form['start_min']))
                publish_start = time.strptime(publish_start, '%Y-%m-%d %H:%M')

                page.start_year = int(req.form['start_year'])
                page.start_month = int(req.form['start_month'])
                page.start_day = int(req.form['start_day'])
                page.start_hour = int(req.form['start_hour'])
                page.start_min = int(req.form['start_min'])
            else:
                publish_start = time.localtime()
            
            if (req.form.has_key('end_year') and req.form['end_year']
                and req.form.has_key('end_month') and req.form['end_month']
                and req.form.has_key('end_day') and req.form['end_day']
                and req.form.has_key('end_hour') and req.form['end_hour']
                and req.form.has_key('end_min') and req.form['end_min']):
                publish_end = '%4d-%02d-%02d %02d:%02d' % (
                 int(req.form['end_year']), int(req.form['end_month']),
                 int(req.form['end_day']), int(req.form['end_hour']),
                 int(req.form['end_min']))
                publish_end = time.strptime(publish_end, '%Y-%m-%d %H:%M')

                page.end_year = int(req.form['end_year'])
                page.end_month = int(req.form['end_month'])
                page.end_day = int(req.form['end_day'])
                page.end_hour = int(req.form['end_hour'])
                page.end_min = int(req.form['end_min'])
            else:
                publish_end = time.localtime(int(time.time()) + 7*24*60*60)

            if publish_start > publish_end:
                page.errors.append('Publish end is before start.')

            if req.form.has_key('maint_tasks'):
                maint_tasks = req.form['maint_tasks']
                if type(maint_tasks) is not list:
                    maint_tasks = [maint_tasks]
                try:
                    maint_tasks.remove('none')
                except ValueError, error:
                    pass
                page.maint_tasks = maint_tasks

            author = req.session['user'].login
            replaces_message = False

            if len(page.errors) == 0:
                # Insert message
                msgid = messages2.setMsg(title, description, tech_description,
                 publish_start, publish_end, author, replaces_message)

                # Connect with task
                for taskid in maint_tasks:
                    messages2.setMsgTask(msgid, int(taskid))

                # Redirect to view?id=$newid and exit
                req.headers_out['location'] = 'view?id=' + str(msgid)
                req.status = apache.HTTP_MOVED_TEMPORARILY
                req.send_http_header()
                return apache.OK
    elif section == 'expire':
        page = Messages2ListTemplate()
        page.title = 'Create New Message'
        page.tasks = maintenance2.getTasks(['maint_end > now()'])
        page.submit = req.form.has_key('new-do')
    else:
        page = Messages2ListTemplate()
        page.title = 'Active Messages'
        page.msgs = messages2.getMsgs(['publish_start < now()', 'publish_end > now()'])

    # Create menu
    page.menu = [{'link': 'active', 'text': 'Active', 'admin': False},
                {'link': 'planned', 'text': 'Planned', 'admin': False},
                {'link': 'historic', 'text': 'Historic', 'admin': False},
                {'link': 'new', 'text': 'Create new', 'admin': True}]
    page.current = section
  
    # Done, output the page
    req.content_type = 'text/html'
    req.send_http_header()
    req.write(page.respond())
    return apache.OK
