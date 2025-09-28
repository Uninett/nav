# -*- coding: utf-8 -*-
#
# Copyright (C) 2008-2009 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

# FIXME
# Errors should not be registered on locations and rooms.
# Either:
# 	- remove support for those
# 	- post alerts on every device found under that room/location

from django.db import transaction

from nav.web.auth.utils import get_account
from nav.models.manage import Room, Netbox, Module
from nav.models.event import EventQueue, EventQueueVar, EventType, Subsystem
from nav.web.message import Messages

STATE_NONE = 'x'
STATE_START = 's'
STATE_END = 'e'

_ = lambda a: a


@transaction.atomic()
def register_error_events(request, **kwargs):
    messages = Messages(request)

    # Get the username of this user.
    account = get_account(request)
    username = account.login

    # Selection must be a dictionary.
    # Recognized keys are 'location', 'room', 'netbox' and 'module'.
    # The values should be simple lists with the ID of the device.
    selection = kwargs.pop('selection', [])

    # The comment for this error.
    comment = kwargs.pop('comment', None)

    # Additional information for the event. Default values should do the trick
    # here, unless you really know what you are doing.
    source = kwargs.pop('source', 'deviceManagement')
    target = kwargs.pop('target', 'eventEngine')
    severity = kwargs.pop('severity', 3)
    state = kwargs.pop('state', STATE_NONE)
    event_type = kwargs.pop('event_type', 'deviceNotice')
    alert_type = kwargs.pop('alert_type', 'deviceError')

    for key in kwargs:
        raise TypeError(
            'register_error_events() got an unexpected keyword argument %s' % key
        )

    # Data that will be inserted into the eventq table.
    default_eventq_data = {
        'source': Subsystem.objects.get(name=source),
        'target': Subsystem.objects.get(name=target),
        'device': None,
        'netbox': None,
        'subid': None,
        'event_type': EventType.objects.get(id=event_type),
        'state': state,
        'severity': severity,
    }

    # Data that will be inserted into the eventqvar table.
    default_eventqvar_data = {
        'alerttype': alert_type,
        'comment': comment,
        'username': username,
    }

    for type in selection:
        if type == 'location':
            devices = selection[type]
        elif type == 'room':
            devices = Room.objects.select_related('location').filter(
                id__in=selection[type]
            )
        elif type == 'netbox':
            devices = Netbox.objects.select_related('room', 'room__location').filter(
                id__in=selection[type]
            )
        elif type == 'module':
            devices = Module.objects.select_related(
                'device', 'netbox', 'netbox__room', 'netbox__room__location'
            ).filter(id__in=selection[type])
        else:
            continue

        for device in devices:
            eventq_data = default_eventq_data.copy()
            eventqvar_data = default_eventqvar_data.copy()
            eventqvar_data['unittype'] = type

            if type == 'location':
                eventqvar_data['locationid'] = device
            elif type == 'room':
                eventqvar_data['roomid'] = device.id
                eventqvar_data['locationid'] = device.location.id
            elif type == 'netbox':
                eventq_data['netbox'] = device
                eventqvar_data['roomid'] = device.room.id
                eventqvar_data['locationid'] = device.room.location.id
            elif type == 'module':
                eventq_data['subid'] = device.id
                eventq_data['netbox'] = device.netbox
                eventq_data['device'] = device.device
                eventqvar_data['roomid'] = device.netbox.room.id
                eventqvar_data['locationid'] = device.netbox.room.location.id

            new_event = EventQueue.objects.create(**eventq_data)
            for key in eventqvar_data:
                EventQueueVar.objects.create(
                    event_queue=new_event, variable=key, value=eventqvar_data[key]
                )

            messages.append(
                {
                    'message': _('Registered error on %(type)s %(device)s.')
                    % {
                        'type': type,
                        'device': device,
                    },
                    'type': Messages.SUCCESS,
                }
            )

    messages.save()
