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
from django.db.models import Q

from nav.models.manage import Room, Location, Netbox, Module
from nav.models.event import AlertHistory, AlertHistoryVariable, AlertHistoryMessage, AlertType

def get_messages(alert):
    # Regular messages
    msgs = AlertHistoryMessage.objects.filter(
        alert_history=alert,
        type='sms',
        language='en',
    )
    msgs_list = [m.message for m in msgs]

    return msgs_list

class History:
    locations = []
    rooms = []
    netboxes = []
    modules = []

    start_time = []
    end_time = []
    types = []

    def __init__(self, **kwargs):
        selection = kwargs.pop('selection', [])
        self.start_time = kwargs.pop('start_time', date.fromtimestamp(time.time() - 7 * 24 * 60 * 60))
        self.end_time = kwargs.pop('end_time', date.today())
        self.types = kwargs.pop('types', None)

        for key in kwargs.keys():
            raise TypeError('__init__() got an unexpected keyword argument %s' % key)

        self.locations = selection.get('location', [])
        self.rooms = selection.get('room', [])
        self.netboxes = selection.get('netbox', [])
        self.modules = selection.get('module', [])

        self.time_limit = [
            Q(start_time__lte=self.end_time) &
            (
                Q(end_time__gte=self.start_time) |
                (
                    Q(end_time__isnull=True) &
                    Q(start_time__gte=self.start_time)
                )
            )
        ]

    def get_location_history(self):
        alert_history = AlertHistory.objects.select_related(
            'event_type', 'alert_type'
        ).filter(
            Q(device__netbox__room__location__id__in=self.locations),
            *self.time_limit
        ).extra(
            select={
                'location_id': 'location.locationid',
                'location_name': 'location.descr',
            },
            tables=['location'],
            where=['location.locationid=room.locationid']
        ).order_by('location_name', '-start_time', '-end_time')

        if self.types['event']:
            alert_history = alert_history.filter(event_type__in=self.types['event'])
        if self.types['alert']:
            alert_history = alert_history.filter(alert_type__in=self.types['alert'])

        history = {}
        for a in alert_history:
            if a.location_id not in history:
                history[a.location_id] = {
                    'description': a.location_name,
                    'alerts': []
                }
            history[a.location_id]['alerts'].append({
                'alert': a,
                'messages': get_messages(alert=a),
            })
        return history

    def get_room_history(self):
        alert_history = AlertHistory.objects.select_related(
            'event_type', 'alert_type'
        ).filter(
            Q(device__netbox__room__id__in=self.rooms),
            *self.time_limit
        ).extra(
            select={
                'room_id': 'room.roomid',
                'room_descr': 'room.descr',
           },
           tables=['room'],
           where=['room.roomid=netbox.roomid']
        ).order_by('alerthistoryvariable__value', '-start_time', '-end_time')

        if self.types['event']:
            alert_history = alert_history.filter(event_type__in=self.types['event'])
        if self.types['alert']:
            alert_history = alert_history.filter(alert_type__in=self.types['alert'])

        history = {}
        for a in alert_history:
            if a.room_id not in history:
                if not isinstance(a.room_id, unicode):
                    a.room_id = unicode(a.room_id)
                if not isinstance(a.room_descr, unicode):
                    a.room_descr = unicode(a.room_descr)
                history[a.room_id] = {
                    'description': a.room_id + ' (' + a.room_descr + ')',
                    'alerts': []
                }

            history[a.room_id]['alerts'].append({
                'alert': a,
                'messages': get_messages(alert=a),
            })

        return history

    def get_netbox_history(self):
        alert_history = AlertHistory.objects.select_related(
            'event_type', 'alert_type'
        ).filter(
            Q(device__netbox__id__in=self.netboxes),
            *self.time_limit
        ).extra(
            select={
                'netbox_id': 'netbox.netboxid',
                'netbox_name': 'netbox.sysname',
            },
            tables=['netbox'],
            where=['netbox.deviceid=device.deviceid']
        ).order_by('-start_time')

        if self.types['event']:
            alert_history = alert_history.filter(event_type__in=self.types['event'])
        if self.types['alert']:
            alert_history = alert_history.filter(alert_type__in=self.types['alert'])

        history = {}
        for a in alert_history:
            if a.netbox_id not in history:
                history[a.netbox_id] = {
                    'description': a.netbox_name,
                    'alerts': []
                }
            history[a.netbox_id]['alerts'].append({
                'alert': a,
                'messages': get_messages(alert=a),
            })

        return history

    def get_module_history(self):
        alert_history = AlertHistory.objects.select_related(
            'event_type', 'alert_type'
        ).filter(
            Q(device__module__id__in=self.modules),
            *self.time_limit
        ).extra(
            select={
                'module': 'module.module',
                'netbox_name': 'netbox.sysname',
            },
            tables=['module', 'netbox'],
            where=['module.deviceid=device.deviceid', 'netbox.netboxid=module.netboxid']
        ).order_by('-start_time')

        if self.types['event']:
            alert_history = alert_history.filter(event_type__in=self.types['event'])
        if self.types['alert']:
            alert_history = alert_history.filter(alert_type__in=self.types['alert'])

        history = {}
        for a in alert_history:
            if a.module not in history:
                history[a.module] = {
                    'description': u'Module %i in %s' %  (a.module, a.netbox_name),
                    'alerts': []
                }
            history[a.module]['alerts'].append({
                'alert': a,
                'messages': get_messages(alert=a),
            })

        return history
