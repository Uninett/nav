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
from nav.models.event import AlertHistory, AlertHistoryVariable, AlertType, EventType
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
    expand_message = int(request.GET.get('expand', 0))

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
    params = {
        'selection': selection,
        'start_time': from_date,
        'end_time': to_date,
        'types': selected_types,
    }
    history = History(**params)

    # We want to re-use this request in some of the links.
    # This little double-loop builds a string that is easy to add to links.
    filter_string = ''
    for key in request.GET:
        if key != 'expand':
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
        'history': {
            'location': history.get_location_history(),
            'room': history.get_room_history(),
            'netbox': history.get_netbox_history(),
            'module': history.get_module_history(),
        },
        'selection': selection,
        'selected_types': selected_types,
        'event_type': event_types,
        'from_date': from_date,
        'to_date': to_date,
        'filter_string': filter_string,
        'expand_message': expand_message,
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
