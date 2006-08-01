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
        section = 'all'

    # Create section page
    if section == 'active':
        page = Messages2ListTemplate()
        page.title = 'Active Messages'
        page.msgs = getMsgs(['publish_start < now()', 'publish_end > now()'])
    elif section == 'planned':
        page = Messages2ListTemplate()
        page.title = 'Planned Messages'
        page.msgs = getMsgs(['publish_start > now()'])
    elif section == 'historic':
        page = Messages2ListTemplate()
        page.title = 'Historic Messages'
        page.msgs = getMsgs(['publish_end < now()'])
    elif section == 'view' and args.get('id').isdigit():
        page = Messages2ListTemplate()
        page.title = 'Message'
        viewid = int(args.get('id'))
        page.msgs = getMsgs(['messageid = %d' % viewid])
    elif section == 'new':
        page = Messages2NewTemplate()
        page.title = 'Create New Message'
        page.tasks = getTasks(['maint_end > now()'])
        page.submit = req.form.has_key('new-do')
        if page.submit:
            page.errors = []
            if req.form.has_key('title') and req.form['title']:
                title = req.form['title']
            else:
                page.errors.append('You did not supply a title.')

            if req.form.has_key('description') and req.form['description']:
                description = req.form['description']
            else:
                page.errors.append('You did not supply a description.')

            if req.form.has_key('tech_description') and len(req.form['tech_description']) > 0:
                tech_description = req.form['tech_description']
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
            else:
                publish_end = time.localtime(int(time.time()) + 7*24*60*60)

            if req.form.has_key('maint_tasks'):
                maint_tasks = req.form['maint_tasks']
                if type(maint_tasks) is not list:
                    maint_tasks = [maint_tasks]
                maint_tasks.remove('none')

            author = req.session['user'].login
            replaces_message = False

            if len(page.errors) == 0:
                # Insert message
                newid = setMsg(title, description, tech_description,
                 publish_start, publish_end, author, replaces_message)

                # Connect with task
                for taskid in maint_tasks:
                    pass

                # Redirect to view?id=$newid and exit
                req.headers_out['location'] = 'view?id=' + str(newid)
                req.status = apache.HTTP_MOVED_TEMPORARILY
                req.send_http_header()
                return apache.OK
            else:
                # Print errors
                pass # FIXME
    else:
        page = Messages2ListTemplate()
        page.title = 'All messages'
        page.msgs = getMsgs()

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
