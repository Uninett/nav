#
# Copyright (C) 2006-2008, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import time
import datetime

from django.http import HttpResponse
from django.shortcuts import redirect

import nav.messages
import nav.maintenance
from nav.web.templates.MessagesListTemplate import MessagesListTemplate
from nav.web.templates.MessagesDetailsTemplate import MessagesDetailsTemplate
from nav.web.templates.MessagesNewTemplate import MessagesNewTemplate
from nav.web.templates.MessagesFeedTemplate import MessagesFeedTemplate
from nav.web.encoding import encoded_output
from nav.django.utils import get_account

def rss(req):
    page = MessagesFeedTemplate()
    page.msgs = nav.messages.getMsgs('publish_start < now() AND publish_end > now() AND replaced_by IS NULL')

    page.channeltitle = 'NAV Message Feed from ' + req.META['HTTP_HOST']
    page.channeldesc = page.channeltitle
    page.channellink = 'http://' + req.META['HTTP_HOST'] + req.path
    page.channellang = 'en-us'
    page.channelttl = '60'

    page.pubDate = datetime.datetime(year=1900, month=1, day=1)
    for i, msg in enumerate(page.msgs):
        if msg['publish_start'] > page.pubDate:
            page.pubDate = msg['publish_start']
        page.msgs[i]['link'] = 'http://' + req.META['HTTP_HOST'] \
            + '/messages/view?id=' + str(page.msgs[i]['messageid'])
        page.msgs[i]['guid'] = page.msgs[i]['link']
    if page.pubDate == 0:
        page.pubDate = datetime.datetime.now()

    return HttpResponse(page.respond(), mimetype='application/xml')

def planned(req):
    section = get_section(req)

    page = MessagesListTemplate()
    page.title = 'Planned Messages'
    page.msgs = nav.messages.getMsgs('publish_start > now() AND publish_end > now() AND replaced_by IS NULL')
    return build_menu_and_return(req, page, section)

def historic(req):
    section = get_section(req)

    page = MessagesListTemplate()
    page.title = 'Historic Messages'
    page.msgs = nav.messages.getMsgs('publish_end < now() OR replaced_by IS NOT NULL', 'publish_end DESC')

    return build_menu_and_return(req, page, section)

def view(req):
    section = get_section(req)

    page = MessagesDetailsTemplate()
    page.title = 'Message'
    menu_dict = {'link': 'view', 'text': 'View', 'admin': False}
    msgid = int(req.REQUEST.get('id'))
    page.msgs = nav.messages.getMsg(msgid)

    return build_menu_and_return(req, page, section, menu_dict)

def expire(req):
    section = get_section(req)

    page = MessagesDetailsTemplate()
    page.title = 'Expire message'
    menu_dict = {'link': 'expire', 'text': 'Expire', 'admin': True}
    page.infomsgs = []
    msgid = int(req.REQUEST.get('id'))
    nav.messages.expireMsg(msgid)
    page.infomsgs.append('The following message was expired.')
    page.msgs = nav.messages.getMsg(msgid)

    return build_menu_and_return(req, page, section, menu_dict)

def new(req):
    section = get_section(req)

    page = MessagesNewTemplate()
    page.title = 'Create New Message'
    page.tasks = nav.maintenance.getTasks('maint_end > now()')
    page.errors = []
    
    page.submit = req.REQUEST.has_key('submit')
    if page.submit:
        return submit_form(req, page, section)
    
    return build_menu_and_return(req, page, section)

def edit(req):
    section = get_section(req)

    page = MessagesNewTemplate()
    page.title = 'Edit Message'
    page.submittext = 'Save Message'
    page.tasks = nav.maintenance.getTasks('maint_end > now()')
    page.errors = []

    menu_dict = {'link': 'edit', 'text': 'Edit', 'admin': True}

    if not req.REQUEST.get('id'):
        page.errors.append('Message ID in request is not a digit.')
    else:
        msgid = int(req.REQUEST.get('id'))
        msg = nav.messages.getMsg(msgid)[0]

        page.edit_messageid = msgid
        page.formtitle = msg['title']
        page.description = msg['description']
        page.tech_description = msg['tech_description']

        page.start_year = int(msg['publish_start'].strftime('%Y'))
        page.start_month = int(msg['publish_start'].strftime('%m'))
        page.start_day = int(msg['publish_start'].strftime('%d'))
        page.start_hour = int(msg['publish_start'].strftime('%H'))
        page.start_min = int(msg['publish_start'].strftime('%M'))

        page.end_year = int(msg['publish_end'].strftime('%Y'))
        page.end_month = int(msg['publish_end'].strftime('%m'))
        page.end_day = int(msg['publish_end'].strftime('%d'))
        page.end_hour = int(msg['publish_end'].strftime('%H'))
        page.end_min = int(msg['publish_end'].strftime('%M'))

        if type(msg['replaces_message']) is int:
            page.replaces_messageid = msg['replaces_message']
            page.replaces_message = \
                nav.messages.getMsg(page.replaces_messageid)[0]
        else:
            page.replaces_messageid = False

        if type(msg['tasks']) is list:
            page.maint_tasks = []
            for task in msg['tasks']:
                page.maint_tasks.append(str(task['maint_taskid']))
        else:
            page.maint_tasks = []
    
    page.submit = req.REQUEST.has_key('submit')
    if page.submit:
        return submit_form(req, page, section, menu_dict)

    return build_menu_and_return(req, page, section, menu_dict)

def followup(req):
    section = get_section(req)

    page = MessagesNewTemplate()
    page.title = 'Create New Message'
    page.tasks = nav.maintenance.getTasks('maint_end > now()')
    page.errors = []
    page.current = 'new' # Just to mark the menu tab
    if not req.REQUEST.get('id'):
        page.errors.append('Message ID in request is not a digit.')
    else:
        msgid = int(req.REQUEST.get('id'))
        page.replaces_messageid = msgid

        msg = nav.messages.getMsg(msgid)[0]
        page.replaces_message = msg
        page.formtitle = msg['title']

        page.start_year = int(msg['publish_start'].strftime('%Y'))
        page.start_month = int(msg['publish_start'].strftime('%m'))
        page.start_day = int(msg['publish_start'].strftime('%d'))
        page.start_hour = int(msg['publish_start'].strftime('%H'))
        page.start_min = int(msg['publish_start'].strftime('%M'))

        page.end_year = int(msg['publish_end'].strftime('%Y'))
        page.end_month = int(msg['publish_end'].strftime('%m'))
        page.end_day = int(msg['publish_end'].strftime('%d'))
        page.end_hour = int(msg['publish_end'].strftime('%H'))
        page.end_min = int(msg['publish_end'].strftime('%M'))

    page.submit = req.REQUEST.has_key('submit')
    if page.submit:
        return submit_form(req, page, section)

    return build_menu_and_return(req, page, section)

def active(req):
    section = get_section(req)

    page = MessagesListTemplate()
    page.title = 'Active Messages'
    page.msgs = nav.messages.getMsgs('publish_start < now() AND publish_end > now() AND replaced_by IS NULL')

    return build_menu_and_return(req, page, section)

### Helpers ###
def build_menu_and_return(req, page, section, menu_dict=None):
    """ User login, menu building and return with HttpResponse object """
    # Check if user is logged in
    account = get_account(req)
    if account.has_perm(None, None):
        page.authorized = True
    else:
        page.authorized = False

    menu = []
    menu.append({'link': 'active', 'text': 'Active', 'admin': False})
    menu.append({'link': 'planned', 'text': 'Planned', 'admin': False})
    menu.append({'link': 'historic', 'text': 'Historic', 'admin': False})

    if menu_dict:
        menu.append(menu_dict)

    page.menu = menu
    if page.authorized:
        page.menu.append({'link': 'new', 'text': 'Create new', 'admin': True})

    if not page.hasVar('current'):
        page.current = section
    if not page.hasVar('submittext'):
        page.submittext = page.title

    return HttpResponse(page.respond())

def submit_form(req, page, section, menu_dict=None):
    """ Form submission which redirects to view of submitted data """    
    menu = []
    menu.append({'link': 'active', 'text': 'Active', 'admin': False})
    menu.append({'link': 'planned', 'text': 'Planned', 'admin': False})
    menu.append({'link': 'historic', 'text': 'Historic', 'admin': False})

    if menu_dict:
        menu.append(menu_dict)

    # Form submitted
    page.submit = req.REQUEST.has_key('submit')
    if page.submit:
        # Get and control form data
        if req.REQUEST.has_key('title') and req.REQUEST['title']:
            title = req.REQUEST['title']
            page.formtitle = title
        else:
            page.errors.append('You did not supply a title.')

        # Descriptions
        if req.REQUEST.has_key('description') and req.REQUEST['description']:
            description = req.REQUEST['description']
            page.description = description
        else:
            page.errors.append('You did not supply a description.')

        if req.REQUEST.has_key('tech_description') and len(req.REQUEST['tech_description']) > 0:
            tech_description = req.REQUEST['tech_description']
            page.tech_description = tech_description
        else:
            tech_description = False

        # Publish times
        if (req.REQUEST.has_key('start_year') and req.REQUEST['start_year']
            and req.REQUEST.has_key('start_month') and req.REQUEST['start_month']
            and req.REQUEST.has_key('start_day') and req.REQUEST['start_day']
            and req.REQUEST.has_key('start_hour') and req.REQUEST['start_hour']
            and req.REQUEST.has_key('start_min') and req.REQUEST['start_min']):
            publish_start = '%4d-%02d-%02d %02d:%02d' % (
                int(req.REQUEST['start_year']), int(req.REQUEST['start_month']),
                int(req.REQUEST['start_day']), int(req.REQUEST['start_hour']),
                int(req.REQUEST['start_min']))
            publish_start = time.strptime(publish_start, '%Y-%m-%d %H:%M')

            page.start_year = int(req.REQUEST['start_year'])
            page.start_month = int(req.REQUEST['start_month'])
            page.start_day = int(req.REQUEST['start_day'])
            page.start_hour = int(req.REQUEST['start_hour'])
            page.start_min = int(req.REQUEST['start_min'])
        else:
            publish_start = time.localtime()
        
        if (req.REQUEST.has_key('end_year') and req.REQUEST['end_year']
            and req.REQUEST.has_key('end_month') and req.REQUEST['end_month']
            and req.REQUEST.has_key('end_day') and req.REQUEST['end_day']
            and req.REQUEST.has_key('end_hour') and req.REQUEST['end_hour']
            and req.REQUEST.has_key('end_min') and req.REQUEST['end_min']):
            publish_end = '%4d-%02d-%02d %02d:%02d' % (
                int(req.REQUEST['end_year']), int(req.REQUEST['end_month']),
                int(req.REQUEST['end_day']), int(req.REQUEST['end_hour']),
                int(req.REQUEST['end_min']))
            publish_end = time.strptime(publish_end, '%Y-%m-%d %H:%M')

            page.end_year = int(req.REQUEST['end_year'])
            page.end_month = int(req.REQUEST['end_month'])
            page.end_day = int(req.REQUEST['end_day'])
            page.end_hour = int(req.REQUEST['end_hour'])
            page.end_min = int(req.REQUEST['end_min'])
        else:
            publish_end = time.localtime(int(time.time()) + 7*24*60*60)

        if publish_start >= publish_end:
            page.errors.append('Publish end is before or same as start, ' \
                + 'message will never be published.')
        
        # Maintenance tasks
        if req.REQUEST.has_key('maint_tasks'):
            maint_tasks = req.REQUEST['maint_tasks']
            if type(maint_tasks) is not list:
                maint_tasks = [maint_tasks]
            try:
                maint_tasks.remove('none')
            except ValueError, error:
                pass
            page.maint_tasks = maint_tasks
        else:
            maint_tasks = []

        # Followup
        if req.REQUEST.has_key('replaces_messageid') \
            and req.REQUEST['replaces_messageid']:
            replaces_messageid = int(req.REQUEST['replaces_messageid'])
            page.replaces_messageid = replaces_messageid
        else:
            replaces_messageid = False

        # Get ID of message edited
        if section == 'edit':
            if req.REQUEST.has_key('edit_messageid') \
                and req.REQUEST['edit_messageid']:
                edit_messageid = int(req.REQUEST['edit_messageid'])
            else:
                page.errors.append('ID of edited message is missing.')

        # Get session data
        author = req._req.session['user']['login']

        # If any data not okay, form is showed with list of errors on top.
        # There is no need to do anything further here.
        if len(page.errors):
            pass
        # No errors, update database
        else:
            if section == 'edit':
                msgid = edit_messageid
            else:
                msgid = False

            # Update/Insert message
            msgid = nav.messages.setMsg(msgid, str(title),
                str(description), str(tech_description), publish_start,
                publish_end, author, replaces_messageid)

            # For updates, remove all existing task connections
            if section == 'edit':
                nav.messages.removeMsgTasks(msgid)

            # Connect with task
            for taskid in maint_tasks:
                nav.messages.setMsgTask(msgid, int(taskid))

            return redirect('/messages/view?id=' + str(msgid))

def get_section(args):
    """ Helper to get section you are in. Ex: 'active' """
    # Get section
    if len(args.path.split('/')[-1]):
        return args.path.split('/')[-1]

    return 'active'
