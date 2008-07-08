# -*- coding: ISO8859-1 -*-
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
#
# Authors: Thomas Adamcik <thomas.adamcik@uninett.no>
#

__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Thomas Adamcik (thomas.adamcik@uninett.no)"
__id__ = "$Id$"

from django.template.loader import get_template
from django.template import Context

from nav.models.manage import Location, Room, Netbox, Module
from nav.models.service import Service

class QuickSelect:
    def __init__(self, prefix='', location=True, room=True, netbox=True, service=False, module=False):
        self.location = location
        self.room = room
        self.netbox = netbox
        self.service = service
        self.module = module

        self.location_set = Location.objects.order_by(('id')).values()
        self.service_set = Service.objects.order_by('handler').values()
        self.netbox_set = Netbox.objects.order_by('sysname').values()
        self.module_set = Module.objects.order_by('module_number').values()
        self.room_set = Room.objects.order_by('id').values()

        self.prefix = prefix
        self.output = []

    def handle_post(self, request):
        result = {
            'location': [],
            'service': [],
            'netbox': [],
            'module': [],
            'room': [],
        }

        if self.prefix:
            location = 'submit_%s_location' % prefix
            service = 'submit_%s_service' % prefix
            module = 'submit_%s_location' % prefix
            netbox = 'submit_%s_netbox' % prefix
            room = 'submit_%s_room' % prefix
        else:
            location = 'submit_location'
            service = 'submit_service'
            module = 'submit_location'
            netbox = 'submit_netbox'
            room = 'submit_room'

        if self.location and request.form.has_key(location):
            result['location'] = request.form.getlist(location[7:])

        if self.room and request.form.has_key(room):
            result['room'] = request.form.getlist(room[7:])

        if self.netbox and request.form.has_key(netbox):
            result['netbox'] = request.form.getlist(netbox[7:])

        if self.service and request.form.has_key(service):
            result['service'] = request.form.getlist(service[7:])

        if self.module and request.form.has_key(module):
            result['module'] = request.form.getlist(module[7:])

        return result

    def __str__(self):
        if not self.output:
            prefix = self.prefix
            output = []
            location_name = {}
            room_name = {}
            netbox_name = {}

            if self.location:
                locations = {'': []}
                for location in self.location_set:
                    location_name[location['id']] = '%(id)s (%(description)s)' % location
                    locations[''].append((location['id'], location_name[location['id']]))

                if prefix:
                    name = '%s_%s' % (prefix, 'location')
                else:
                    name = 'location'

                output.append({
                        'label': 'Location',
                        'name': name,
                        'collapse': True,
                        'objects': sorted(locations.iteritems()),
                    })

            if self.room:
                rooms = {}
                for room in self.room_set:
                    location = location_name.get(room['location_id'])
                    room_name[room['id']] = '%(id)s (%(description)s)' % room
                    if location in rooms:
                        rooms[location].append((room['id'], room_name[room['id']]))
                    else:
                        rooms[location] = [(room['id'], room_name[room['id']])]

                if prefix:
                    name = '%s_%s' % (prefix, 'room')
                else:
                    name = 'room'

                output.append({
                        'label': 'Room',
                        'name': name,
                        'collapse': True,
                        'objects': sorted(rooms.iteritems()),
                    })

            if self.netbox:
                netboxes = {}
                for netbox in self.netbox_set:
                    room = room_name.get(netbox['room_id'])
                    netbox_name[netbox['id']] = '%(sysname)s' % netbox
                    if room in netboxes:
                        netboxes[room].append((netbox['id'], netbox_name[netbox['id']]))
                    else:
                        netboxes[room] = [(netbox['id'], netbox_name[netbox['id']])]

                if prefix:
                    name = '%s_%s' % (prefix, 'netbox')
                else:
                    name = 'netbox'

                output.append({
                        'label': 'IP device',
                        'name': name,
                        'objects': sorted(netboxes.iteritems()),
                    })

            if self.service:
                services = {}
                for service in self.service_set:
                    netbox = netbox_name[service['netbox_id']]
                    name = '%(handler)s' % service
                    if netbox in services:
                        services[netbox].append((service['id'], name))
                    else:
                        services[netbox] = [(service['id'], name)]

                if prefix:
                    name = '%s_%s' % (prefix, 'service')
                else:
                    name = 'service'

                output.append({
                        'label': 'Service',
                        'name': name,
                        'collapse': True,
                        'objects': sorted(services.iteritems()),
                    })

            if self.module:
                modules = {}
                for module in self.module_set:
                    netbox = netbox_name[module['netbox_id']]
                    name = '%(module_number)s' % module
                    if netbox in modules:
                        modules[netbox].append((module['id'], name))
                    else:
                        modules[netbox] = [(module['id'], name)]

                if prefix:
                    name = '%s_%s' % (prefix, 'module')
                else:
                    name = 'module'

                output.append({
                        'label': 'Module',
                        'name': name,
                        'collapse': True,
                        'objects': sorted(modules.iteritems()),
                    })
            self.output = output

        template = get_template('webfront/quickselect.html')
        context  = Context({'output': output})

        return template.render(context)
