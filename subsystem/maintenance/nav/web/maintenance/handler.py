#! /usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2006-2008 UNINETT AS
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
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#          Thomas Adamcik <thomas.adamcik@uninett.no>
#

"""
mod_python handler for Maintenance subsystem.
"""

__copyright__ = "Copyright 2006-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no), Thomas Adamcik (thomas.adamcik@uninett.no)"
__id__ = "$Id:$"

import time
from mod_python import apache, util

import nav.db
import nav.maintenance
from nav.web.URI import URI
from nav.web.templates.MaintenanceCalTemplate import MaintenanceCalTemplate
from nav.web.templates.MaintenanceDetailsTemplate import MaintenanceDetailsTemplate
from nav.web.templates.MaintenanceListTemplate import MaintenanceListTemplate
from nav.web.templates.MaintenanceNewTemplate import MaintenanceNewTemplate
from nav.web.quickselect import QuickSelect

dbconn = nav.db.getConnection('webfront', 'manage')
db = dbconn.cursor()

def handler(req):
    """Handler for the Maintenance subsystem."""

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

    # Create initial menu, more is appended depending on context
    menu = []
    menu.append({'link': 'calendar', 'text': 'Calendar', 'admin': False})
    menu.append({'link': 'active', 'text': 'Active', 'admin': False})
    menu.append({'link': 'planned', 'text': 'Planned', 'admin': False})
    menu.append({'link': 'historic', 'text': 'Historic', 'admin': False})

    ### SECTIONS
    # Show active maintenance tasks (public tasks)
    if section == 'active':
        page = MaintenanceListTemplate()
        page.title = 'Active Maintenance Tasks'
        page.tasks = nav.maintenance.getTasks('maint_start < now() AND maint_end > now()')

    # Planned maintenance tasks (not yet reached activation time)
    elif section == 'planned':
        page = MaintenanceListTemplate()
        page.title = 'Planned Maintenance Tasks'
        page.tasks = nav.maintenance.getTasks('maint_start > now() AND maint_end > now()')

    # Historic maintenance tasks
    elif section == 'historic':
        page = MaintenanceListTemplate()
        page.title = 'Historic Maintenance Tasks'
        page.tasks = nav.maintenance.getTasks('maint_end < now()', 'maint_end DESC')

    # View a maintenance task
    elif section == 'view' and args.get('id'):
        page = MaintenanceDetailsTemplate()
        page.title = 'Maintenance Task'
        menu.append({'link': 'view', 'text': 'View', 'admin': False})
        taskid = int(args.get('id'))
        page.tasks = nav.maintenance.getTask(taskid)

    # Cancel a maintenance task
    elif section == 'cancel' and args.get('id'):
        page = MaintenanceDetailsTemplate()
        page.title = 'Cancel maintenance task'
        menu.append({'link': 'cancel', 'text': 'Cancel', 'admin': True})
        page.infomsgs = []
        taskid = int(args.get('id'))
        nav.maintenance.cancelTask(taskid)
        page.infomsgs.append('The following maintenance task was canceled.')
        page.tasks = nav.maintenance.getTask(taskid)

    # New and edit
    elif section == 'new' or section =='edit':
        page = MaintenanceNewTemplate()
        page.title = 'Create New Maintenance Task'
        page.action = "new"
        page.errors = []
        page.components = []

        page.quickselect = QuickSelect(service=True)

        # Edit: Fill page with existing data
        if section == 'edit':
            page.title = 'Edit Maintenance Task'
            page.submittext = 'Save Maintenance Task'
            menu.append({'link': 'edit', 'text': 'Edit', 'admin': True})

            if not args.get('id') or not args.get('id').isdigit():
                page.errors.append('Maintenance task ID in request is not a digit.')
            else:
                taskid = int(args.get('id'))
                page.action = "edit?id=%d" % taskid
                task = nav.maintenance.getTask(taskid)[0]
                page.edit_taskid = taskid

                # Maintenance components
                page.components = task['components']

                # Maintenance times
                page.start_year = int(task['maint_start'].strftime('%Y'))
                page.start_month = int(task['maint_start'].strftime('%m'))
                page.start_day = int(task['maint_start'].strftime('%d'))
                page.start_hour = int(task['maint_start'].strftime('%H'))
                page.start_min = int(task['maint_start'].strftime('%M'))

                page.end_year = int(task['maint_end'].strftime('%Y'))
                page.end_month = int(task['maint_end'].strftime('%m'))
                page.end_day = int(task['maint_end'].strftime('%d'))
                page.end_hour = int(task['maint_end'].strftime('%H'))
                page.end_min = int(task['maint_end'].strftime('%M'))

                # Description
                page.description = task['description']


        # Init components
        if req.form.has_key('component-0'):
            # Use submitted data instead of defaults or the components from the
            # task we are editing
            components = []
            for field in req.form.list:
                if field.name[:len('component')] == 'component':
                    key, value = field.value.split(',')
                    components.append({'key': key, 'value': value,
                        'info': nav.maintenance.getComponentInfo(key, value)})
        else:
            # Nothing submitted, using values from default or the task we are
            # editing
            components = page.components

        # Handle added components
        for key,values in page.quickselect.handle_post(req).iteritems():
            for v in values:
                component = {
                    'key': key,
                    'value': v,
                    'info': nav.maintenance.getComponentInfo(key, v),
                }
                if components.count(component) == 0:
                    components.append(component)

        # Handle removed components
        if req.form.has_key('submit_comp_remove'):
            for field in req.form.list:
                if field.name[:len('remove')] == 'remove':
                    key, value = field.value.split(',')
                    components.remove({'key': key, 'value': value,
                        'info': nav.maintenance.getComponentInfo(key, value)})

        # Fill page with components
        components = nav.maintenance.sortComponents(components)
        page.components = components


        # For any non-final submit button pressed, keep entered dates and
        # descriptions (> 1 because of edit?id=X)
        page.submit = (len(req.form.list) > 1
            and not req.form.has_key('submit_final'))
        if page.submit:
            # Maintenance times
            page.start_year = int(req.form['start_year'])
            page.start_month = int(req.form['start_month'])
            page.start_day = int(req.form['start_day'])
            page.start_hour = int(req.form['start_hour'])
            page.start_min = int(req.form['start_min'])

            page.end_year = int(req.form['end_year'])
            page.end_month = int(req.form['end_month'])
            page.end_day = int(req.form['end_day'])
            page.end_hour = int(req.form['end_hour'])
            page.end_min = int(req.form['end_min'])

            # Description
            page.description = req.form['description']

        # Form submitted: prepare rest of the needed data
        page.submit = req.form.has_key('submit_final')
        if page.submit:
            # Maintenance components
            if (req.form.has_key('component-0') and req.form['component-0']):
                pass # components already contains everything we want
            else:
                page.errors.append('No maintenance components selected.')
            
            # Maintenance times
            if (req.form.has_key('start_year') and req.form['start_year']
                and req.form.has_key('start_month') and req.form['start_month']
                and req.form.has_key('start_day') and req.form['start_day']
                and req.form.has_key('start_hour') and req.form['start_hour']
                and req.form.has_key('start_min') and req.form['start_min']):
                maint_start = '%4d-%02d-%02d %02d:%02d' % (
                    int(req.form['start_year']), int(req.form['start_month']),
                    int(req.form['start_day']), int(req.form['start_hour']),
                    int(req.form['start_min']))
                maint_start = time.strptime(maint_start, '%Y-%m-%d %H:%M')

                page.start_year = int(req.form['start_year'])
                page.start_month = int(req.form['start_month'])
                page.start_day = int(req.form['start_day'])
                page.start_hour = int(req.form['start_hour'])
                page.start_min = int(req.form['start_min'])
            else:
                maint_start = time.localtime()

            if (req.form.has_key('end_year') and req.form['end_year']
                and req.form.has_key('end_month') and req.form['end_month']
                and req.form.has_key('end_day') and req.form['end_day']
                and req.form.has_key('end_hour') and req.form['end_hour']
                and req.form.has_key('end_min') and req.form['end_min']):
                maint_end = '%4d-%02d-%02d %02d:%02d' % (
                    int(req.form['end_year']), int(req.form['end_month']),
                    int(req.form['end_day']), int(req.form['end_hour']),
                    int(req.form['end_min']))
                maint_end = time.strptime(maint_end, '%Y-%m-%d %H:%M')

                page.end_year = int(req.form['end_year'])
                page.end_month = int(req.form['end_month'])
                page.end_day = int(req.form['end_day'])
                page.end_hour = int(req.form['end_hour'])
                page.end_min = int(req.form['end_min'])
            else:
                maint_end = time.localtime(int(time.time()) + 7*24*60*60)

            if maint_start >= maint_end:
                page.errors.append('Maintenance end is before or same as ' \
                    + 'start, task will never be scheduled.')

            # Description
            if req.form.has_key('description') and req.form['description']:
                description = req.form['description']
                page.description = description
            else:
                page.errors.append('You did not supply a description.')

            # Edit task 
            if (req.form.has_key('edit_taskid')
                and req.form['edit_taskid'].isdigit()):
                # Get ID of edited message
                taskid = int(req.form['edit_taskid'])
                edit_task = nav.maintenance.getTask(taskid)[0]

                # Find new state
                now = time.localtime()
                if maint_start >= now:
                    state = 'scheduled'
                elif maint_start < now:
                    if maint_end > now:
                        state = 'scheduled'
                    elif maint_end <= now:
                        state = 'passed'
            # New task
            else:
                taskid = False
                state = 'scheduled'

            # Get session data
            author = req.session['user']['login']

            # If any data not okay, form is showed with list of errors on top.
            # There is no need to do anything further here.
            if len(page.errors):
                pass
            # No errors, update database
            else:
                # Update/insert maintenance task
                taskid = nav.maintenance.setTask(taskid, maint_start,
                    maint_end, description, author, state)

                # Update/insert maintenance components
                compstatus = nav.maintenance.setComponents(taskid, components)
                if not compstatus:
                    page.error.append('Failed adding components.')

                # Redirect to view?id=$newid and exit
                req.headers_out['location'] = 'view?id=' + str(taskid)
                req.status = apache.HTTP_MOVED_TEMPORARILY
                req.send_http_header()
                return apache.OK

    # Default section: Show task calendar
    else:
        page = MaintenanceCalTemplate()
        page.title = 'Maintenance Schedule'

        # Get input arguments
        if args.get('y'):
            page.year = int(args.get('y'))
        else:
            page.year = int(time.strftime('%Y'))
        if args.get('m'):
            page.month = int(args.get('m'))
        else:
            page.month = int(time.strftime('%m'))

        # Get tasks
        tasks = nav.maintenance.getTasks("maint_start > '%04d-%02d-01'" \
            % (page.year, page.month), 'maint_start') or []
        
        # Group tasks by start date
        page.tasks = {}
        for task in tasks:
            date = task['maint_start'].strftime('%Y-%m-%d')
            if not page.tasks.has_key(date):
                page.tasks[date] = []
            page.tasks[date].append(task)
        

    # Check if user is logged in
    if req.session['user']['id'] != 0:
        page.authorized = True
    else:
        page.authorized = False

    # Push menu to page
    page.menu = menu
    if page.authorized:
        page.menu.append({'link': 'new', 'text': 'Create new', 'admin': True})

    if not page.hasVar('current'):
        page.current = section
    if not page.hasVar('submittext'):
        page.submittext = page.title
   
    # Done, output the page
    req.content_type = 'text/html'
    req.send_http_header()
    req.write(page.respond())
    return apache.OK
