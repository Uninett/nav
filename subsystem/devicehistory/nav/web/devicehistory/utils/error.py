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

from django.db.models import Q

from nav.models.manage import Room, Location, Netbox, Module
from nav.models.event import EventQueue, EventQueueVar

class RegisterEvent:
    STATE_NONE = 'x'
    STATE_START = 's'
    STATE_END = 'e'

    events = []
    eventq_data = {}
    evenqvar_data = {}

    def __init__(self, **kwargs):
        self.selection = kwargs.pop('selection', [])
        self.comment = kwargs.pop('comment', None)
        self.username = request._reg['user'].login

        self.source = kwargs.pop('source', 'deviceManagement')
        self.target = kwargs.pop('target', 'eventEngine')
        self.severity = kwargs.pop('severity', 0)
        self.state = kwargs.pop('state', self.STATE_NONE)
        self.event_type = kwargs.pop('event_type', 'deviceNotice')
        self.alert_type = kwargs.pop('alert_type', 'deviceError')

        for key in kwargs.keys():
            raise TypeError('__init__() got an unexpected keyword argument %s' % key)

        self.eventq_data = {
            'source': self.source,
            'target': self.target
            'device': None,
            'netbox': None,
            'subid': None,
            'event_type': self.event_type,
            'state': self.state,
            'severity': self.severity,
        }

        self.eventqvar_data = {
            'alerttype': self.alert_type,
            'comment': self.comment,
            'username': self.username,
        }

        if 'location' in self.selection and len(self.selection['location']) > 0:
            self._register_location_error()
        if 'room' in self.selection and len(self.selection['room']) > 0:
            self._register_room_error()
        if 'netbox' in self.selection and len(self.selection['netbox']) > 0:
            self._register_netbox_error()
        if 'module' in self.selection and len(self.selection['module']) > 0:
            self._register_module_error()

    def _register_location_error(self):
        for dev in selection['location']:
            eventqvar_data = self.evetqvar_data
            eventqvar_data['unittype'] = 'location'
            eventqvar_data['locationid'] = dev

            self._register_error(self.eventq_data, eventqvar_data)

    def _register_room_error(self):
        for dev in selection['room']:
            eventqvar_data = self.evetqvar_data
            eventqvar_data['unittype'] = 'room'
            eventqvar_data['locationid'] = dev

            self._register_error(self.eventq_data, eventqvar_data)

    def _register_netbox_error(self):
        boxes = Netbox.objects.filter(id__in=selection['netbox'])
        for netbox in boxes:
            eventq_data = self.eventq_data
            eventq_data['netbox'] = netbox.id
            eventq_data['device'] = netbox.device.id

            eventqvar_data = self.eventqvar_data

    def _register_module_error(self):
        pass

    def _register_error(self, evetq_data, eventqvar_data):
        self.events.append(EventQueue.create(**eventq_data))
        for key, value in eventqvar_data.items():
            EventQueueVar.create(
                event_queue=event.id, variable=key, value=value)
