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
from django.db.models import Q

from nav.models.manage import Room, Location, Netbox, Module
from nav.models.event import AlertHistory, AlertHistoryVariable

LOCATION_HISTORY_TYPE = 'location'
ROOM_HISTORY_TYPE = 'room'
NETBOX_HISTORY_TYPE = 'netbox'
MODULE_HISTORY_TYPE = 'module'

# History is ordered like this:
#
# history = {
#    'descripton': 'Descriptuion of this type',
#    'history': a_list_of_alerts_of_the_same_type
# }
#
# a_list_of_alerts_of_the_same_type contains alert dictionaries like this:
#
# alert = {
#     'alert': the_alert_history_django_model_element,
#     'messages': english_sms_that_belongs_to_this_alert
# }

def get_history(selection):
    history = {}
    if LOCATION_HISTORY_TYPE in selection and len(selection[LOCATION_HISTORY_TYPE]) > 0:
        history[LOCATION_HISTORY_TYPE] = get_location_history(selection[LOCATION_HISTORY_TYPE])
    if ROOM_HISTORY_TYPE in selection and len(selection[ROOM_HISTORY_TYPE]) > 0:
        history[ROOM_HISTORY_TYPE] = get_room_history(selection[ROOM_HISTORY_TYPE])
    if NETBOX_HISTORY_TYPE in selection and len(selection[NETBOX_HISTORY_TYPE]) > 0:
        history[NETBOX_HISTORY_TYPE] = get_netbox_history(selection[NETBOX_HISTORY_TYPE])
    if MODULE_HISTORY_TYPE in selection and len(selection[MODULE_HISTORY_TYPE]) > 0:
        history[MODULE_HISTORY_TYPE] = get_module_history(selection[MODULE_HISTORY_TYPE])

    return history

def get_location_history(locations):
    alert_history = AlertHistory.objects.filter(
        alerthistoryvariable__variable='locationid',
        alerthistoryvariable__value__in=locations
    ).extra(
        select={
            'location_id': 'location.locationid',
            'location_name': 'location.descr',
        },
        tables=['location'],
        where=['location.locationid=alerthistvar.val']
    ).order_by('location_name', '-start_time', '-end_time')

    history = {}
    for a in alert_history:
        if a.location_id not in history:
            history[a.location_id] = DescriptiveList(description=a.location_name)
        history[a.location_id].append(Alert(alert=a))
    return history

def get_room_history(rooms):
    alert_history = AlertHistory.objects.filter(
        alerthistoryvariable__variable='roomid',
        alerthistoryvariable__value__in=rooms
    ).extra(
        select={
            'room_id': 'room.roomid',
            'room_descr': 'room.descr',
       },
       tables=['room'],
       where=['room.roomid=alerthistvar.val']
    ).order_by('alerthistoryvariable__value', '-start_time', '-end_time')

    history = {}
    for a in alert_history:
        if a.room_id not in history:
            if not isinstance(a.room_id, unicode):
                a.room_id = unicode(a.room_id)
            if not isinstance(a.room_descr, unicode):
                a.room_descr = unicode(a.room_descr)
            descr = a.room_id + ' (' + a.room_descr + ')'
            history[a.room_id] = DescriptiveList(description=descr)
        history[a.room_id].append(Alert(alert=a))
    return history

def get_netbox_history(netboxes):
    alert_history = AlertHistory.objects.filter(
        device__netbox__id__in=netboxes,
    ).extra(
        select={
            'netbox_id': 'netbox.netboxid',
            'netbox_name': 'netbox.sysname',
        },
        tables=['netbox'],
        where=['netbox.deviceid=device.deviceid']
    ).order_by('-start_time')

    history = {}
    for a in alert_history:
        if a.netbox_id not in history:
            history[a.netbox_id] = DescriptiveList(description=a.netbox_name)
        history[a.netbox_id].append(Alert(alert=a))
    return history

def get_module_history(modules):
    alert_history = AlertHistory.objects.filter(
        device__module__id__in=modules,
    ).extra(
        select={'module': 'module.moduleid'},
        tables=['module'],
        where=['module.deviceid=device.deviceid']
    ).order_by('-start_time')

    history = {}
    for a in alert_history:
        if a.module not in history:
            history[a.module] = DescriptiveList(description=Netbox.objects.get(module=a.module))
        history[a.module].append(Alert(alert=a))
    return history


class DescriptiveList(list):
    description = None

    def __init__(self, *args, **kwargs):
        self.description = kwargs.pop('description', None)
        self.history = kwargs.pop('history', [])

        super(DescriptiveList, self).__init__(*args, **kwargs)

class Alert:
    alert = None
    messages = []

    def __init__(self, **kwargs):
        self.alert = kwargs.pop('alert', None)

        for key in kwargs.keys():
            raise TypeError('__init__() got an unexpected keyword argument %s' % key)

        self.messages = self.alert.messages.filter(type='sms', language='en')
