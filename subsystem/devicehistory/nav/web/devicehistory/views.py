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
from django.db import connection
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.utils.datastructures import SortedDict

from nav.django.context_processors import account_processor
from nav.django.shortcuts import render_to_response, object_list
from nav.models.manage import Room, Location, Netbox, Module
from nav.models.event import AlertHistory, AlertHistoryMessage, \
    AlertHistoryVariable, AlertType, EventType
from nav.web.message import new_message, Messages
from nav.web.templates.DeviceHistoryTemplate import DeviceHistoryTemplate
from nav.web.quickselect import QuickSelect

from nav.web.devicehistory.utils import get_event_and_alert_types
from nav.web.devicehistory.utils.history import get_selected_types, \
    fetch_history, get_page, get_messages_for_history, \
    group_history_and_messages
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

_ = lambda a: a

# NOTE:
# Search is using POST instead of GET, which would be more correct, because of
# constraints in IE that limits the length of an URL to around 2000 characters.

def devicehistory_search(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_view_history_kwargs)
    from_date = request.POST.get('from_date', date.fromtimestamp(time.time() - ONE_WEEK))
    to_date = request.POST.get('to_date', date.fromtimestamp(time.time() + ONE_DAY))
    types = request.POST.getlist('type')

    selected_types = get_selected_types(types)
    event_types = get_event_and_alert_types()

    info_dict = {
        'active': {'devicesearch': True},
        'quickselect': DeviceQuickSelect,
        'selected_types': selected_types,
        'event_type': event_types,
        'from_date': from_date,
        'to_date': to_date,
    }
    return render_to_response(
        DeviceHistoryTemplate,
        'devicehistory/history_search.html',
        info_dict,
        RequestContext(
            request,
            processors=[account_processor]
        )
    )

def devicehistory_view(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_view_history_kwargs)
    from_date = request.POST.get('from_date', date.fromtimestamp(time.time() - ONE_WEEK))
    to_date = request.POST.get('to_date', date.fromtimestamp(time.time() + ONE_DAY))
    types = request.POST.getlist('type')
    group_by = request.POST.get('group_by', 'netbox')

    selection = DeviceQuickSelect.handle_post(request)
    selected_types = get_selected_types(types)
    event_types = get_event_and_alert_types()

    try:
        page = int(request.POST.get('page', '1'))
    except ValueError:
        page = 1

    alert_history = fetch_history(
        selection,
        from_date,
        to_date,
        selected_types,
        group_by
    )
    paginated_history = Paginator(alert_history, HISTORY_PER_PAGE)
    this_page = get_page(paginated_history, page)
    messages = get_messages_for_history(this_page.object_list)
    grouped_history = group_history_and_messages(
        this_page.object_list,
        messages,
        group_by
    )
    this_page.grouped_history = grouped_history

    info_dict = {
        'active': {'devicehistory': True},
        'history': this_page,
        'selection': selection,
        'selected_types': selected_types,
        'event_type': event_types,
        'from_date': from_date,
        'to_date': to_date,
        'group_by': group_by,
    }
    return render_to_response(
        DeviceHistoryTemplate,
        'devicehistory/history_view.html',
        info_dict,
        RequestContext(
            request,
            processors=[account_processor]
        )
    )

def error_form(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_post_error_kwargs)
    if request.method == 'POST':
        return register_error(request)

    info_dict = {
        'active': {'error': True},
        'quickselect': DeviceQuickSelect,
    }
    return render_to_response(
        DeviceHistoryTemplate,
        'devicehistory/register_error.html',
        info_dict,
        RequestContext(
            request,
            processors=[account_processor]
        )
    )

def register_error(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_post_error_kwargs)
    selection = DeviceQuickSelect.handle_post(request)
    error_comment = request.POST.get('error_comment', None)

    register_error_events(request, selection=selection, comment=error_comment)

    return HttpResponseRedirect(reverse('devicehistory-registererror'))

def delete_module(request):
    params = []
    confirm_deletion = False
    if request.method == 'POST':
        module_ids = request.POST.getlist('module')
        params.append('module.moduleid IN (%s)' % ",".join([id for id in module_ids]))
        confirm_deletion = True

    cursor = connection.cursor()
    cursor.execute("""SELECT
            sysname,
            moduleid,
            module.descr AS descr,
            start_time,
            NOW() - start_time AS downtime
        FROM module
        INNER JOIN netbox ON (module.netboxid = netbox.netboxid)
        LEFT OUTER JOIN alerthist ON (
            module.deviceid = alerthist.deviceid OR
            module.netboxid = alerthist.netboxid
        )
        WHERE
            module.up = 'n' AND
            alerthist.end_time = 'infinity' AND
            alerthist.eventtypeid = 'moduleState'""")

    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            'sysname': row[0],
            'moduleid': row[1],
            'descr': row[2],
            'start_time': row[3],
            'downtime': row[4],
        })

    info_dict = {
        'active': {'module': True},
        'confirm_delete': confirm_deletion,
        'modules': result
    }
    return render_to_response(
        DeviceHistoryTemplate,
        'devicehistory/delete_module.html',
        info_dict,
        RequestContext(
            request,
            processors=[account_processor]
        )
    )

def do_delete_module(request):
    if request.method != 'POST' or not request.POST.get('confirm_delete', False):
        return HttpResponseRedirect(reverse('devicehistory-module'))

    module_ids = request.POST.getlist('module')
    params = [
        'module.moduleid IN (%s)' % ",".join([id for id in module_ids])
    ]

    history = AlertHistory.objects.extra(
        select={
            'module': 'module.moduleid',
        },
        tables=[
            'device',
            'module',
            'netbox',
        ],
        where=[
            'device.deviceid=alerthist.deviceid',
            'module.deviceid=device.deviceid',
            'netbox.netboxid=module.netboxid',
            'module.up=\'n\'',
            'alerthist.end_time=\'infinity\'',
            'alerthist.eventtypeid=\'moduleState\'',
        ] + params
    )

    if history.count() == 0:
        new_message(
            request,
            _('No modules selected'),
            Messages.NOTICE
        )
        return HttpResponseRedirect(reverse('devicehistory-module'))

    # FIXME should there be posted an event, telling the event/alert system
    # that this module is now deleted?
    modules = Module.objects.filter(id__in=[id for module in history])

    new_message(
        request,
        _('Deleted selected modules.'),
        Messages.SUCCESS,
    )

    modules.delete()

    return HttpResponseRedirect(reverse('devicehistory-module'))
