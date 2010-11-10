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

import time
from datetime import date, datetime

from django.core.paginator import Paginator
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.datastructures import SortedDict

from nav.models.manage import Room, Location, Netbox, Module
from nav.models.event import AlertHistory, AlertHistoryMessage, \
    AlertHistoryVariable, AlertType, EventType
from nav.web.message import new_message, Messages
from nav.web.quickselect import QuickSelect

from nav.web.devicehistory.utils import get_event_and_alert_types
from nav.web.devicehistory.utils.history import get_selected_types, \
    fetch_history, get_page, get_messages_for_history, \
    group_history_and_messages, describe_search_params, check_empty_selection
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
        'location': request.REQUEST.getlist('loc'),
        'room': request.REQUEST.getlist('room'),
        'netbox': request.REQUEST.getlist('netbox'),
        'module': request.REQUEST.getlist('module'),
    }
    selection = check_empty_selection(selection)

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
    params = {}
    confirm_deletion = False
    if request.method == 'POST':
        module_ids = request.POST.getlist('module')
        params['id__in'] = module_ids
        confirm_deletion = True

    # Find modules that are down.
    modules_down = Module.objects.select_related(
        'device', 'netbox'
    ).filter(
        up='n',
        **params
    )

    # Find all moduleStates with no end time that are related to the modules we
    # found.
    history = AlertHistory.objects.select_related(
        'device', 'netbox'
    ).filter(
        Q(device__in=[d.device.id for d in modules_down]) |
        Q(netbox__in=[d.netbox.id for d in modules_down]),
        event_type__id='moduleState',
        alert_type__id=8,
        end_time__gt=datetime.max
    )

    # Sew the results together.
    result = []
    for a in modules_down:
        for b in history:
            if a.device.id == b.device.id or a.netbox.id == b.netbox.id:
                result.append({
                    'sysname': a.netbox.sysname,
                    'moduleid': a.id,
                    'name': a.name,
                    'module_number': a.module_number,
                    'descr': a.description,
                    'start_time': b.start_time,
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

def do_delete_module(request):
    if request.method != 'POST' or not request.POST.get('confirm_delete', False):
        return HttpResponseRedirect(reverse('devicehistory-module'))

    module_ids = request.POST.getlist('module')
    params = {'id__in': module_ids}

    # Find modules that are down.
    modules_down = Module.objects.select_related(
        'device', 'netbox'
    ).filter(
        up='n',
        **params
    )

    # Find all moduleStates with no end time that are related to the modules we
    # found. We use it to check that the supplied modules acctually are down.
    history = AlertHistory.objects.select_related(
        'device', 'netbox'
    ).filter(
        Q(device__in=[d.device.id for d in modules_down]) |
        Q(netbox__in=[d.netbox.id for d in modules_down]),
        event_type__id='moduleState',
        alert_type__id=8,
        end_time__gt=datetime.max
    )

    if history.count() == 0:
        new_message(request._req,
            _('No modules selected'),
            Messages.NOTICE
        )
        return HttpResponseRedirect(reverse('devicehistory-module'))

    # FIXME should there be posted an event, telling the event/alert system
    # that this module is now deleted?

    new_message(request._req,
        _('Deleted selected modules.'),
        Messages.SUCCESS,
    )

    cursor = connection.cursor()
    cursor.execute("DELETE FROM module WHERE moduleid IN %s", (tuple([m.id for m in modules_down]),))
    transaction.commit_unless_managed()

    return HttpResponseRedirect(reverse('devicehistory-module'))
