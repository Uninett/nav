# -*- coding: utf-8 -*-
#
# Copyright 2008 UNINETT AS
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
# Authors: Magnus Motzfeldt Eide <magnus.eide@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Magnus Motzfeldt Eide (magnus.eide@uninett.no)"
__id__ = "$Id$"

import time
from datetime import date
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template import RequestContext

from nav.django.context_processors import account_processor
from nav.django.shortcuts import render_to_response, object_list
from nav.models.manage import Room, Location, Netbox, Module
from nav.models.event import AlertHistory, AlertHistoryMessage, AlertHistoryVariable, AlertType, EventType
from nav.web.message import new_message, Messages
from nav.web.templates.DeviceHistoryTemplate import DeviceHistoryTemplate
from nav.web.quickselect import QuickSelect

from nav.web.devicehistory.utils.history import History
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

_ = lambda a: a

def devicehistory_search(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_view_history_kwargs)
    info_dict = {
        'active': {'devicehistory': True},
        'quickselect': DeviceQuickSelect,
    }
    return render_to_response(
        DeviceHistoryTemplate,
        'devicehistory/history_search.html',
        info_dict,
        RequestContext(
            request,
            processors=[account_processor]
        )
    );

def devicehistory_view(request):
    DeviceQuickSelect = QuickSelect(**DeviceQuickSelect_view_history_kwargs)

    # Default dates are a little hackish.
    # from_date defaults to one week in the past.
    # to_date defaults to tomorrow, which means "everything untill tomorrow
    # starts". Setting it to today will not display the alerts for today.
    from_date = request.GET.get('from_date', date.fromtimestamp(time.time() - 7 * 24 * 60 * 60))
    to_date = request.GET.get('to_date', date.fromtimestamp(time.time() + 24 * 60 * 60))
    types = request.GET.getlist('type')

    selected_types = {'event': [], 'alert': []}
    for type in types:
        if type.find('_') != -1:
            splitted = type.split('_')
            if splitted[0] == 'e':
                selected_types['event'].append(splitted[1])
            else:
                selected_types['alert'].append(splitted[1])

    # FIXME check that date is a valid "yyyy-mm-dd" string

    selection = DeviceQuickSelect.handle_post(request)

    # Fetch history for selected items.
    # Also fetches additional info about location, room, netbox and module.
    alert_history = AlertHistory.objects.select_related(
        'event_type', 'alert_type', 'device'
    ).filter(
        Q(device__netbox__room__location__id__in=selection['location']) |
        Q(device__netbox__room__id__in=selection['room']) | 
        Q(device__netbox__id__in=selection['netbox']) |
        Q(device__module__id__in=selection['module']),
        Q(start_time__lte=to_date) &
        (
            Q(end_time__gte=from_date) |
            (
                Q(end_time__isnull=True) &
                Q(start_time__gte=from_date)
            )
        )
    ).extra(
        select={
            'location_id': 'location.locationid',
            'location_name': 'location.descr',
            'room_id': 'room.roomid',
            'room_descr': 'room.descr',
            'netbox_id': 'netbox.netboxid',
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
    )

    # Fetch related messages
    msgs = AlertHistoryMessage.objects.filter(
        alert_history__in=alert_history,
        language='en',
        type='sms',
    )

    history = {}
    for a in alert_history:
        loc_id = a.location_name
        room_id = a.room_id
        room_descr = a.room_descr
        device_serial = a.device.serial
        box_id = a.netbox_id
        module_name = a.module_name

        if loc_id not in history:
            history[loc_id] = {
                'description': a.location_name,
                'rooms': {},
            }
        if room_id not in history[loc_id]['rooms']:
            if not isinstance(room_id, unicode):
                room_id = unicode(room_id)
            if not isinstance(room_descr, unicode):
                room_descr = unicode(room_descr)
            history[loc_id]['rooms'][room_id] = {
                'description': room_id + u' (' + room_descr + u')',
                'netboxes': {},
                'devices': {},
            }
        if device_serial not in history[loc_id]['rooms'][room_id]['devices']:
            history[loc_id]['rooms'][room_id]['devices'][device_serial] = {
                'description': device_serial,
                'alerts': []
            }
        if box_id not in history[loc_id]['rooms'][room_id]['netboxes']:
            history[loc_id]['rooms'][room_id]['netboxes'][box_id] = {
                'description': a.netbox_name,
                'modules': {},
                'alerts': []
            }
        if module_name not in history[loc_id]['rooms'][room_id]['netboxes'][box_id]['modules']:
            history[loc_id]['rooms'][room_id]['netboxes'][box_id]['modules'][module_name] = {
                'description': module_name,
                'alerts': []
            }

        alert_messages = []
        for m in msgs:
            if m.alert_history_id == a.id:
                alert_messages.append(m)

        a.extra_messages = alert_messages

        if a.device.serial:
            history[loc_id]['rooms'][room_id]['devices'][device_serial]['alerts'].append(a)
        if a.netbox_id:
            history[loc_id]['rooms'][room_id]['netboxes'][box_id]['alerts'].append(a)
        if a.module_name:
            history[loc_id]['rooms'][room_id]['netboxes'][box_id]['modules'][module_name]['alerts'].append(a)

    # We want to re-use this request in some of the links.
    # This little double-loop builds a string that is easy to add to links.
    filter_string = ''
    for key in request.GET:
        for value in request.GET.getlist(key):
            if not filter_string:
                filter_string = '?%s=%s' % (key,value)
            else:
                filter_string += '&%s=%s' % (key,value)

    alert_types = AlertType.objects.select_related(
        'event_type'
    ).all().order_by('event_type__id', 'name')
    event_types = {}
    for a in alert_types:
        if a.event_type.id not in event_types:
            event_types[a.event_type.id] = []
        event_types[a.event_type.id].append(a)

    info_dict = {
        'active': {'devicehistory': True},
        'history': history,
#        'history': {
#            'location': history.get_location_history(),
#            'room': history.get_room_history(),
#            'netbox': history.get_netbox_history(),
#            'module': history.get_module_history(),
#        },
        'selection': selection,
        'selected_types': selected_types,
        'event_type': event_types,
        'from_date': from_date,
        'to_date': to_date,
        'filter_string': filter_string,
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
    );

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

    modules = AlertHistory.objects.extra(
        select={
            'module_id': 'module.moduleid',
            'module': 'module.module',
            'module_description': 'module.descr',
            'netbox_name': 'netbox.sysname',
            'downtime': 'NOW() - alerthist.start_time',
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
    ).order_by('start_time')

    info_dict = {
        'active': {'module': True},
        'confirm_delete': confirm_deletion,
        'modules': modules,
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
