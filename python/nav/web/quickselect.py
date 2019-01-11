# -*- coding: utf-8 -*-
#
# Copyright (C) 2008 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""QuickSelect widget for use in various web forms."""

from django.template.loader import get_template
from django.template import Context
from django.utils.six import iteritems
from django.utils.encoding import python_2_unicode_compatible

from nav.models.manage import Location, Room, Netbox, Module, NetboxGroup
from nav.models.service import Service


@python_2_unicode_compatible
class QuickSelect(object):
    """Class for presenting and handling a quickselect form"""

    def __init__(self, **kwargs):
        self.button = kwargs.pop('button', 'Add %s')

        self.location = kwargs.pop('location', True)
        self.room = kwargs.pop('room', True)
        self.netbox = kwargs.pop('netbox', True)
        self.netboxgroup = kwargs.pop('netboxgroup', True)
        self.service = kwargs.pop('service', False)
        self.module = kwargs.pop('module', False)

        self.location_label = kwargs.pop('location_label',
                                         '%(id)s (%(description)s)')
        self.room_label = kwargs.pop('room_label',
                                     '%(id)s (%(description)s)')
        self.netbox_label = kwargs.pop('netbox_label', '%(sysname)s')
        self.netboxgroup_label = kwargs.pop('netboxgroup_label', '%(pk)s')
        self.service_label = kwargs.pop('service_label', '%(handler)s')
        self.module_label = kwargs.pop('module_label', '%(name)s')

        self.location_multi = kwargs.pop('location_multiple', True)
        self.room_multi = kwargs.pop('room_multiple', True)
        self.netbox_multi = kwargs.pop('netbox_multiple', True)
        self.netboxgroup_multi = kwargs.pop('netboxgroup_multiple', True)
        self.service_multi = kwargs.pop('service_multiple', True)
        self.module_multi = kwargs.pop('module_multiple', True)

        for key in kwargs.keys():
            raise TypeError('__init__() got an unexpected keyword argument '
                            '%s' % key)

        # 'Dirtier than your mother' hack to add the serial to our values.
        netboxes = Netbox.objects.order_by('sysname')
        self.netbox_set = [netbox for netbox in netboxes.values()]
        for index, netbox in enumerate(netboxes):
            serial = netbox.device.serial if netbox.device else None
            self.netbox_set[index]['device__serial'] = serial

        # Rest of the queryset we need
        self.location_set = Location.objects.order_by(('id')).values()
        self.service_set = Service.objects.order_by('handler').values()
        self.module_set = Module.objects.order_by('module_number').values()
        self.room_set = Room.objects.order_by('id').values()
        self.netboxgroup_set = NetboxGroup.objects.order_by('id').values()

        self.output = []

    def handle_post(self, request):
        """Handles a post request from a quickselect form"""
        # Django requests has post and get data stored in an attribute called
        # REQUEST, while mod_python request stores it in form.
        #
        # This little if/else makes sure we can use both.
        if hasattr(request, 'REQUEST'):
            form = request.REQUEST
        else:
            form = request.form

        result = {
            'location': [],
            'service': [],
            'netbox': [],
            'module': [],
            'room': [],
            'netboxgroup': [],
        }

        for field in result.keys():
            submit = 'submit_%s' % field
            key = field

            if hasattr(request, 'form'):
                form = request.form
            else:
                form = request.REQUEST

            if field == 'location':
                # Hack to work around noscript XSS protection that triggers on
                # location
                key = key.replace('location', 'loc')
                submit = submit.replace('location', 'loc')

            if getattr(self, field):
                if submit in form and key in form:
                    result[field] = form.getlist(key)
                elif 'add_%s' % key in form:
                    result[field] = form.getlist('add_%s' % key)
                elif 'view_%s' % key in form:
                    result[field] = form.getlist('view_%s' % key)
                elif key != field:
                    # Extra check that allows add_loc in addtion to
                    # add_location
                    if 'add_%s' % field in form:
                        result[field] = form.getlist('add_%s' % field)
                    elif 'view_%s' % field in form:
                        result[field] = form.getlist('view_%s' % field)

                if not getattr(self, '%s_multi' % field):
                    # Limit to first element if multi is not set.
                    result[field] = result[field][:1]

        return result

    def __str__(self):
        if not self.output:
            output = []
            location_name = {}
            room_name = {}
            netbox_name = {}

            if self.location:
                locations = {'': []}
                for location in self.location_set:
                    location_name[location['id']] = (self.location_label %
                                                     location)
                    locations[''].append((location['id'],
                                          location_name[location['id']]))

                # use loc instead of location to avoid noscript XSS protection
                output.append({
                        'label': 'Location',
                        'button': self.button % 'location',
                        'multi': self.location_multi,
                        'name': 'loc',
                        'collapse': True,
                        'objects': sorted(iteritems(locations)),
                    })

            if self.room:
                rooms = {}
                for room in self.room_set:
                    location = location_name.get(room['location_id'])
                    room_name[room['id']] = self.room_label % room
                    if location in rooms:
                        rooms[location].append((room['id'],
                                                room_name[room['id']]))
                    else:
                        rooms[location] = [(room['id'], room_name[room['id']])]

                output.append({
                        'label': 'Room',
                        'button': self.button % 'room',
                        'multi': self.room_multi,
                        'name': 'room',
                        'collapse': True,
                        'objects': sorted(iteritems(rooms)),
                    })

            if self.netbox:
                netboxes = {}
                for netbox in self.netbox_set:
                    room = room_name.get(netbox['room_id'])
                    netbox_name[netbox['id']] = self.netbox_label % netbox
                    if room in netboxes:
                        netboxes[room].append((netbox['id'],
                                               netbox_name[netbox['id']]))
                    else:
                        netboxes[room] = [(netbox['id'],
                                           netbox_name[netbox['id']])]

                output.append({
                        'label': 'IP device',
                        'button': self.button % 'IP device',
                        'multi': self.netbox_multi,
                        'name': 'netbox',
                        'objects': sorted(iteritems(netboxes)),
                    })

            if self.netboxgroup:
                netboxgroups = {'': []}
                for netboxgroup in self.netboxgroup_set:
                    netboxgroups[''].append((netboxgroup['id'], netboxgroup['id']))

                output.append({
                        'label': 'Device Group',
                        'button': self.button % 'device group',
                        'multi': self.netboxgroup_multi,
                        'name': 'netboxgroup',
                        'collapse': True,
                        'objects': sorted(iteritems(netboxgroups)),
                    })

            if self.service:
                services = {}
                for service in self.service_set:
                    netbox = netbox_name[service['netbox_id']]
                    name = self.service_label % service
                    if netbox in services:
                        services[netbox].append((service['id'], name))
                    else:
                        services[netbox] = [(service['id'], name)]

                output.append({
                        'label': 'Service',
                        'button': self.button % 'service',
                        'multi': self.service_multi,
                        'name': 'service',
                        'collapse': True,
                        'objects': sorted(iteritems(services)),
                    })

            if self.module:
                modules = {}
                for module in self.module_set:
                    netbox = netbox_name[module['netbox_id']]
                    name = self.module_label % module
                    if netbox in modules:
                        modules[netbox].append((module['id'], name))
                    else:
                        modules[netbox] = [(module['id'], name)]

                output.append({
                        'label': 'Module',
                        'button': self.button % 'module',
                        'multi': self.module_multi,
                        'name': 'module',
                        'collapse': True,
                        'objects': sorted(iteritems(modules)),
                    })

            self.output = output

        template = get_template('webfront/quickselect.html')
        context = Context({'output': self.output})

        return template.render(context)
