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
from nav.models.event import AlertHistory, AlertHistoryVariable, AlertType

class History:
    history = {}

    def __init__(self, **kwargs):
        self.selection = kwargs.pop('selection', [])
        self.start_time = kwargs.pop('start_time', date.fromtimestamp(time.time() - 7 * 24 * 60 * 60))
        self.end_time = kwargs.pop('end_time', date.today())
        self.types = kwargs.pop('types', None)

        self.history = {'location': [], 'room': [], 'netbox': [], 'module': []}

        for key in kwargs.keys():
            raise TypeError('__init__() got an unexpected keyword argument %s' % key)

        self.time_limit = [
            Q(start_time__lte=self.end_time),
            (
                Q(end_time__gte=self.start_time) |
                Q(end_time__isnull=True)
            ),
            Q(start_time__gte=self.start_time)
        ]

        if 'location' in self.selection and len(self.selection['location']) > 0:
            self._get_location_history()
        if 'room' in self.selection and len(self.selection['room']) > 0:
            self._get_room_history()
        if 'netbox' in self.selection and len(self.selection['netbox']) > 0:
            self._get_netbox_history()
        if 'module' in self.selection and len(self.selection['module']) > 0:
            self._get_module_history()

    def _get_location_history(self):
        alert_history = AlertHistory.objects.filter(
            Q(alerthistoryvariable__variable='locationid'),
            Q(alerthistoryvariable__value__in=self.selection['location']),
            *self.time_limit
        ).extra(
            select={
                'location_id': 'location.locationid',
                'location_name': 'location.descr',
            },
            tables=['location'],
            where=['location.locationid=alerthistvar.val']
        ).order_by('location_name', '-start_time', '-end_time')

        if self.types['event']:
            alert_history = alert_history.filter(event_type__in=self.types['event'])
        if self.types['alert']:
            alert_history = alert_history.filter(alert_type__in=self.types['alert'])

        history = {}
        for a in alert_history:
            if a.location_id not in history:
                history[a.location_id] = DeviceList(description=a.location_name)
            history[a.location_id].append(Alert(alert=a))
        self.history['location'] = history

    def _get_room_history(self):
        alert_history = AlertHistory.objects.filter(
            Q(alerthistoryvariable__variable='roomid'),
            Q(alerthistoryvariable__value__in=self.selection['room']),
            *self.time_limit
        ).extra(
            select={
                'room_id': 'room.roomid',
                'room_descr': 'room.descr',
           },
           tables=['room'],
           where=['room.roomid=alerthistvar.val']
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
                descr = a.room_id + ' (' + a.room_descr + ')'
                history[a.room_id] = DeviceList(description=descr)
            history[a.room_id].append(Alert(alert=a))
        self.history['room'] = history

    def _get_netbox_history(self):
        alert_history = AlertHistory.objects.filter(
            Q(device__netbox__id__in=self.selection['netbox']),
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
                history[a.netbox_id] = DeviceList(description=a.netbox_name)
            history[a.netbox_id].append(Alert(alert=a))
        self.history['netbox'] = history

    def _get_module_history(self):
        alert_history = AlertHistory.objects.filter(
            Q(device__module__id__in=self.selection['module']),
            *self.time_limit
        ).extra(
            select={'module': 'module.moduleid'},
            tables=['module'],
            where=['module.deviceid=device.deviceid']
        ).order_by('-start_time')

        if self.types['event']:
            alert_history = alert_history.filter(event_type__in=self.types['event'])
        if self.types['alert']:
            alert_history = alert_history.filter(alert_type__in=self.types['alert'])

        history = {}
        for a in alert_history:
            if a.module not in history:
                history[a.module] = DeviceList(description=Netbox.objects.get(module=a.module))
            history[a.module].append(Alert(alert=a))
        self.history['module'] = history


class DeviceList(list):
    description = None

    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('description', None)
        super(DeviceList, self).__init__(*args, **kwargs)

class Alert:
    alert = None
    messages = []

    def __init__(self, **kwargs):
        self.alert = kwargs.pop('alert', None)

        for key in kwargs.keys():
            raise TypeError('__init__() got an unexpected keyword argument %s' % key)

        self.messages = self.alert.messages.filter(type='sms', language='en')
