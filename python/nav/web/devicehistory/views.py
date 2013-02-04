# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from operator import attrgetter

import time
from datetime import date

from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.models.fields import INFINITY
from nav.models.manage import Netbox, Module
from nav.models.event import AlertHistory
from nav.web.message import new_message, Messages
from nav.web.quickselect import QuickSelect

from django.db.transaction import commit_on_success

from nav.web.devicehistory.utils import get_event_and_alert_types
from nav.web.devicehistory.utils.history import (get_selected_types,
                                                 fetch_history, get_page,
                                                 get_messages_for_history,
                                                 group_history_and_messages,
                                                 describe_search_params)
from nav.web.devicehistory.utils.error import register_error_events

DeviceQuickSelect_view_history_kwargs = {
    'button': 'View %s history',
    'module': True,
    'netbox_label': '%(sysname)s [%(ip)s - %(device__serial)s]',
}
DeviceQuickSelect_post_error_kwargs = {
    'button': 'Add %s error event',
    'location': False,
    'room': False,
    'module': True,
    'netbox_label': '%(sysname)s [%(ip)s - %(device__serial)s]',
}


# Often used timelimits, in seconds:
ONE_DAY = 24 * 3600
ONE_WEEK = 7 * ONE_DAY

HISTORY_PER_PAGE = 100
ORPHANS = 10

_ = lambda a: a

def devicehistory_search(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_view_history_kwargs)
    from_date = request.POST.get('from_date', date.fromtimestamp(time.time() - ONE_WEEK))
    to_date = request.POST.get('to_date', date.fromtimestamp(time.time() + ONE_DAY))
    types = request.POST.get('type', None)
    group_by = request.REQUEST.get('group_by', 'netbox')

    selected_types = get_selected_types(types)
    event_types = get_event_and_alert_types()

    info_dict = {
        'active': {'device': {'search': True}},
        'quickselect': DeviceQuickSelect,
        'selected_types': selected_types,
        'event_type': event_types,
        'from_date': from_date,
        'to_date': to_date,
        'group_by': group_by,
        'navpath': [('Home', '/'), ('Device History', '')],
        'title': 'NAV - Device History',
    }
    return render_to_response(
        'devicehistory/history_search.html',
        info_dict,
        RequestContext(request)
    )

def devicehistory_view(request):
    from_date = request.REQUEST.get('from_date', date.fromtimestamp(time.time() - ONE_WEEK))
    to_date = request.REQUEST.get('to_date', date.fromtimestamp(time.time() + ONE_DAY))
    types = request.REQUEST.get('type', None)
    group_by = request.REQUEST.get('group_by', 'netbox')
    selection = {
        'organization': request.REQUEST.getlist('org'),
        'category': request.REQUEST.getlist('cat'),
        'location': request.REQUEST.getlist('loc'),
        'room': request.REQUEST.getlist('room'),
        'netbox': request.REQUEST.getlist('netbox'),
        'module': request.REQUEST.getlist('module'),
        'mode': request.REQUEST.getlist('mode')
    }

    try:
        page = int(request.REQUEST.get('page', '1'))
    except ValueError:
        page = 1

    selected_types = get_selected_types(types)
    event_types = get_event_and_alert_types()

    alert_history = fetch_history(
        selection,
        from_date,
        to_date,
        selected_types,
        group_by
    )
    paginated_history = Paginator(alert_history, HISTORY_PER_PAGE, ORPHANS)
    this_page = get_page(paginated_history, page)
    messages = get_messages_for_history(this_page.object_list)
    grouped_history = group_history_and_messages(
        this_page.object_list,
        messages,
        group_by
    )
    this_page.grouped_history = grouped_history

    first_page_link = True
    last_page_link = True
    if this_page.paginator.num_pages > 20:
        if page < 6:
            index = 0
            last_index = 10
        else:
            index = page - 6
            last_index = page + 5
        if page >= this_page.paginator.num_pages - 5:
            last_page_link = False
        if page <= 6:
            first_page_link = False
        pages = this_page.paginator.page_range[index:last_index]
    else:
        pages = this_page.paginator.page_range
        first_page_link = False
        last_page_link = False

    url = "?from_date=%s&to_date=%s&type=%s&group_by=%s" % (
        from_date or "", to_date or "", types or "", group_by or "")

    search_description = describe_search_params(selection)

    for key, values in selection.items():
        attr = key
        if key == "location":
            attr = "loc"
        if key == "organization":
            attr = "org"
        if key == "category":
            attr = "cat"
        for id in values:
            url += "&%s=%s" % (attr, id)

    # Quickselect expects 'loc' and not 'location'
    selection['loc'] = selection['location']
    del selection['location']

    info_dict = {
        'active': {'device': {'history': True}},
        'history': this_page,
        'search_description': search_description,
        'pages': pages,
        'first_page_link': first_page_link,
        'last_page_link': last_page_link,
        'selection': selection,
        'selected_types': selected_types,
        'event_type': event_types,
        'from_date': from_date,
        'to_date': to_date,
        'group_by': group_by,
        'get_url': url,
        'title': 'NAV - Device History',
        'navpath': [
            ('Home', '/'),
            ('Device History', reverse('devicehistory-search')),
        ]
    }
    return render_to_response(
        'devicehistory/history_view.html',
        info_dict,
        RequestContext(request)
    )

def error_form(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_post_error_kwargs)
    error_comment = request.POST.get('error_comment', "")

    return render_to_response(
        'devicehistory/register_error.html',
        {
            'active': {'error': True},
            'confirm': False,
            'quickselect': DeviceQuickSelect,
            'error_comment': error_comment,
            'title': 'NAV - Device History - Register error',
            'navpath': [
                ('Home', '/'),
                ('Register error event', ''),
            ]
        },
        RequestContext(request)
    )

def confirm_error_form(request):
    selection = {
        'netbox': request.POST.getlist('netbox'),
        'module': request.POST.getlist('module'),
    }

    netbox = Netbox.objects.select_related(
        'netbox'
    ).filter(id__in=selection['netbox'])
    module = Module.objects.filter(id__in=selection['module'])

    return render_to_response(
        'devicehistory/confirm_error.html',
        {
            'active': {'error': True},
            'confirm': True,
            'netbox': netbox,
            'module': module,
            'title': 'NAV - Device History - Confirm error event',
            'navpath': [
                ('Home', '/'),
                ('Register error event', reverse('devicehistory-registererror')),
            ],
        },
        RequestContext(request)
    )

def register_error(request):
    selection = {
        'netbox': request.POST.getlist('netbox'),
        'module': request.POST.getlist('module'),
    }
    error_comment = request.POST.get('error_comment', None)
    confirmed = request.POST.get('confirm', False)

    if not selection['netbox'] and not selection['module']:
        new_message(request._req,
            _("No devices selected."),
            Messages.WARNING
        )
        return error_form(request)
    if not error_comment and not confirmed:
        new_message(request._req,
            _("There's no error message supplied. Are you sure you want to continue?"),
            Messages.WARNING,
        )
        return confirm_error_form(request)

    register_error_events(request, selection=selection, comment=error_comment)

    return HttpResponseRedirect(reverse('devicehistory-registererror'))

def delete_module(request):
    """Displays a list of modules that are down, offering to delete selected
    ones from the database.

    Also implements a "confirm deletion" version of the page for the posted
    form.

    """
    if request.method == 'POST':
        module_ids = request.POST.getlist('module')
        history = _get_unresolved_module_states(module_ids)
        confirm_deletion = True
    else:
        confirm_deletion = False
        history = _get_unresolved_module_states()

    result = []
    for alert in history:
        if alert.module:
            result.append({
                'sysname': alert.netbox.sysname,
                'moduleid': alert.module.id,
                'name': alert.module.name,
                'module_number': alert.module.module_number,
                'descr': alert.module.description,
                'start_time': alert.start_time,
            })

    info_dict = {
        'active': {'module': True},
        'confirm_delete': confirm_deletion,
        'modules': result,
        'title': 'NAV - Device History - Delete module',
        'navpath': [('Home', '/'), ('Delete module', '')],
    }
    return render_to_response(
        'devicehistory/delete_module.html',
        info_dict,
        RequestContext(request)
    )

@commit_on_success
def do_delete_module(request):
    """Executes an actual database deletion after deletion was confirmed by
    the delete_module() view.

    """
    if request.method != 'POST' or not request.POST.get('confirm_delete', False):
        return HttpResponseRedirect(reverse('devicehistory-module'))

    module_ids = request.POST.getlist('module')
    history = _get_unresolved_module_states(module_ids)

    if not history:
        new_message(request._req,
            _('No modules selected'),
            Messages.NOTICE
        )
        return HttpResponseRedirect(reverse('devicehistory-module'))

    new_message(request._req,
        _('Deleted selected modules.'),
        Messages.SUCCESS,
    )

    cursor = connection.cursor()
    module_ids = tuple(h.module.id for h in history)
    # Delete modules using raw sql to avoid Django's simulated cascading.
    # AlertHistory entries will be closed by a database trigger.
    cursor.execute("DELETE FROM module WHERE moduleid IN %s", (module_ids,))
    transaction.set_dirty()

    return HttpResponseRedirect(reverse('devicehistory-module'))

def _get_unresolved_module_states(limit_to=None):
    """Returns AlertHistory objects for all modules that are currently down.

    Each AlertHistory object will have an extra module attribute,
    which will be the referenced Module instance.

    """
    history = AlertHistory.objects.select_related(
        'device', 'netbox'
    ).filter(
        event_type__id='moduleState',
        alert_type__name='moduleDown',
        end_time__gte=INFINITY
    ).extra(
        select={'module': 'NULL'}
    )

    if limit_to:
        history = history.filter(subid__in=limit_to)

    history = dict((int(h.subid), h) for h in history)
    for module in Module.objects.filter(id__in=history.keys()):
        history[module.id].module = module

    return sorted(history.values(),
                  key=attrgetter('start_time'))
