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
from nav.models.event import EventQueue, EventQueueVar, EventType, Subsystem
from nav.web.message import new_message, Messages

STATE_NONE = 'x'
STATE_START = 's'
STATE_END = 'e'

_ = lambda a: a

def register_error_events(request, **kwargs):
    events = []
    messages = Messages(request)
    username = request._req.session['user'].login

    selection = kwargs.pop('selection', [])
    comment = kwargs.pop('comment', None)

    source = kwargs.pop('source', 'devicehistory')
    target = kwargs.pop('target', 'eventEngine')
    severity = kwargs.pop('severity', 0)
    state = kwargs.pop('state', STATE_NONE)
    event_type = kwargs.pop('event_type', 'deviceNotice')
    alert_type = kwargs.pop('alert_type', 'deviceError')

    for key in kwargs.keys():
        raise TypeError('register_error_events() got an unexpected keyword argument %s' % key)

    eventq_data = {
        'source': Subsystem.objects.get(name=source),
        'target': Subsystem.objects.get(name=target),
        'device': None,
        'netbox': None,
        'subid': None,
        'event_type': EventType.objects.get(id=event_type),
        'state': state,
        'severity': severity,
    }

    eventqvar_data = {
        'alerttype': alert_type,
        'comment': comment,
        'username': username,
    }

    if 'location' in selection and len(selection['location']) > 0:
        for dev in selection['location']:
            var_data = eventqvar_data
            var_data['unittype'] = 'location'
            var_data['locationid'] = dev

            events.append({
                'meta': {
                    'type': 'location',
                    'name': dev,
                },
                'eventq_data': eventq_data,
                'eventqvar_data': var_data,
            })
    if 'room' in selection and len(selection['room']) > 0:
        rooms = Room.objects.select_related(
            'location'
        ).filter(id__in=selection['room'])
        for room in rooms:
            var_data = eventqvar_data
            var_data['unittype'] = 'room'
            var_data['roomid'] = room.id
            var_data['locationid'] = room.location.id

            events.append({
                'meta': {
                    'type': 'room',
                    'name': room,
                },
                'eventq_data': eventq_data,
                'eventqvar_data': var_data,
            })
    if 'netbox' in selection and len(selection['netbox']) > 0:
        boxes = Netbox.objects.select_related(
            'device', 'room', 'room__location'
        ).filter(id__in=selection['netbox'])
        for netbox in boxes:
            data = eventq_data
            data['netbox'] = netbox
            data['device'] = netbox.device

            var_data = eventqvar_data
            var_data['unittype'] = 'netbox'
            var_data['roomid'] = netbox.room.id
            var_data['locationid'] = netbox.room.location.id

            events.append({
                'meta': {
                    'type': 'box',
                    'name': netbox,
                },
                'eventq_data': data,
                'eventqvar_data': var_data,
            })
    if 'module' in selection and len(selection['module']) > 0:
        modules = Module.objects.select_related(
            'device', 'netbox', 'netbox__room', 'netbox__room__location'
        ).filter(id__in=selection['module'])
        for module in modules:
            data = eventq_data
            data['subid'] = module.id
            data['netbox'] = module.netbox
            data['device'] = module.device

            var_data = eventqvar_data
            var_data['unittype'] = 'module'
            var_data['roomid'] = module.netbox.room.id
            var_data['locationid'] = module.netbox.room.location.id

            events.append({
                'meta': {
                    'type': 'module',
                    'name': module,
                },
                'eventq_data': data,
                'eventqvar_data': var_data
            })

    for event in events:
        new_event = EventQueue(**event['eventq_data'])
        new_event.save()
        for key in event['eventqvar_data']:
            event_vars = EventQueueVar(
                event_queue=new_event,
                variable=key,
                value=event['eventqvar_data'][key]
            )
            event_vars.save()
        messages.append({
            'message': _('Registered error on %(type)s %(device)s.') % {
                'type': event['meta']['type'],
                'device': event['meta']['name'],
            },
            'type': Messages.SUCCESS,
        })

    messages.save()
