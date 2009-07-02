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

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.datastructures import SortedDict

from nav.models.event import AlertHistory, AlertHistoryMessage
from nav.web.quickselect import QuickSelect

DeviceQuickSelect_view_history_kwargs = {
    'button': 'View %s history',
    'module': True,
    'netbox_label': '%(sysname)s [%(ip)s - %(device__serial)s]',
}
ONE_DAY = 24 * 3600
ONE_WEEK = 7 * ONE_DAY

def get_selected_types(types):
    selected_types = {'event': [], 'alert': []}
    for type in types:
        if type.find('_') != -1:
            splitted = type.split('_')
            if splitted[0] == 'e':
                selected_types['event'].append(splitted[1])
            else:
                selected_types['alert'].append(splitted[1])
    return selected_types

def fetch_history(selection, from_date, to_date, selected_types=[], order_by=None):
    def type_query_filter(selected_types):
        type_filter = []
        if selected_types['event']:
            type_filter.append(Q(event_type__in=selected_types['event']))
        if selected_types['alert']:
            type_filter.append(Q(alert_type__in=selected_types['alert']))
        return type_filter

    def choose_ordering(group_by):
        if group_by == "location":
            order_by = ["location_name"]
        elif group_by == "room":
            order_by = ["room_descr"]
        elif group_by == "module":
            order_by = ["module_name"]
        elif group_by == "device":
            order_by = ["device"]
        elif group_by == "datetime":
            order_by = []
        else:
            order_by = ["netbox"]
        order_by.append("-start_time")
        order_by.append("-end_time")
        return order_by

    type_filter = type_query_filter(selected_types)
    order_by = choose_ordering(order_by)

    alert_history = AlertHistory.objects.select_related(
        'event_type', 'alert_type', 'device'
    ).filter(
        Q(device__netbox__room__location__id__in=selection['location']) |
        Q(device__netbox__room__id__in=selection['room']) |
        Q(device__netbox__id__in=selection['netbox']) |
        Q(device__netbox__module__id__in=selection['module']),
        Q(start_time__lte=to_date) &
        (
            Q(end_time__gte=from_date) |
            (
                Q(end_time__isnull=True) &
                Q(start_time__gte=from_date)
            )
        ),
        *type_filter
    ).extra(
        select={
            'location_name': 'location.descr',
            'room_descr': 'room.descr',
            'netbox_name': 'netbox.sysname',
            'module_name': 'module.module',
        },
        tables=[
            'location',
        ],
        where=[
            '''(
               room.locationid = location.locationid AND
               netbox.roomid = room.roomid AND
               netbox.deviceid = device.deviceid
            )'''
        ],
    ).order_by(*order_by)
    return alert_history

def get_page(paginator, page):
    try:
        history = paginator.page(page)
    except (EmptyPage, InvalidPage):
        history = paginator.page(paginator.num_pages)
    return history

def get_messages_for_history(alert_history):
    msgs = AlertHistoryMessage.objects.filter(
        alert_history__in=[h.id for h in alert_history],
        language='en',
    ).values('alert_history', 'message', 'type', 'state')
    return msgs

def group_history_and_messages(history, messages, group_by=None):
    def get_grouping_key(a, group_by):
        if group_by == "location":
            key = a.location_name
        elif group_by == "room":
            key = a.room_descr
        elif group_by == "module":
            key = a.module_name
        elif group_by == "device":
            key = a.device.serial
        elif group_by == "datetime":
            key = a.start_time.date().isoformat()
        else:
            key = a.netbox_name
        return key

    grouped_history = SortedDict()
    for a in history:
        a.extra_messages = {}
        for m in messages:
            if a.id == m['alert_history']:
                if not a.extra_messages.has_key(m['state']):
                    a.extra_messages[m['state']] = {
                        'sms': None,
                        'email': None,
                        'jabber': None,
                    }
                a.extra_messages[m['state']][m['type']] = m['message']

        key = get_grouping_key(a, group_by)

        if not grouped_history.has_key(key):
            grouped_history[key] = []
        grouped_history[key].append(a)
    return grouped_history

def devicehistory_url_pack(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_view_history_kwargs)
    from_date = request.POST.get('from_date', date.fromtimestamp(time.time() - ONE_WEEK))
    to_date = request.POST.get('to_date', date.fromtimestamp(time.time() + ONE_DAY))
    types = request.POST.getlist('type')
    group_by = request.POST.get('group_by', 'netbox')
    selection = DeviceQuickSelect.handle_post(request)
    try:
        page = int(request.POST.get('page', '1'))
    except ValueError:
        page = 1

    url = '?l=%(location)s&r=%(room)s&n=%(netbox)s&m=%(module)s' % {
        'location': ",".join(selection['location']),
        'room': ",".join(selection['room']),
        'netbox': ",".join(selection['netbox']),
        'module': ",".join(selection['module']),
    }
    url += '&fd=%(from_date)s&td=%(to_date)s&ty=%(types)s&gb=%(group_by)s&p=%(page)s' % {
        'from_date': from_date,
        'to_date': to_date,
        'types': ",".join(types),
        'group_by': group_by,
        'page': page,
    }
    return reverse('devicehistory-view') + url


def devicehistory_url_unpack(request):
    location =  []
    room = []
    netbox= []
    module = []
    if request.GET.get('l', None):
        location = request.GET.get('l').split(',')
    if request.GET.get('r', None):
        room = request.GET.get('r').split(',')
    if request.GET.get('n', None):
        netbox = request.GET.get('n').split(',')
    if request.GET.get('m', None):
        module = request.GET.get('m').split(',')

    from_date = request.GET.get('fd', date.fromtimestamp(time.time() - ONE_WEEK))
    to_date = request.GET.get('td', date.fromtimestamp(time.time() + ONE_DAY))
    types = request.GET.get('ty', '').split(',')
    group_by = request.GET.get('gb', 'netbox')
    try:
        page = int(request.GET.get('p', '1'))
    except ValueError:
        page = 1

    # Make datetime objects from our date strings
    # In Python 2.5 we can use datetime.strptime(), but for now, this is what
    # we do:
    from_date = datetime(*(time.strptime(from_date, "%Y-%m-%d")[0:6]))
    to_date = datetime(*(time.strptime(to_date, "%Y-%m-%d")[0:6]))

    return {
        'selection': {
            'location': location,
            'room': room,
            'netbox': netbox,
            'module': module,
        },
        'from_date': from_date,
        'to_date': to_date,
        'types': types,
        'group_by': group_by,
        'page': page,
    }
