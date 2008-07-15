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
# Author: Thomas Adamcik <thomas.adamcik@uninett.no>
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
    def __init__(self, prefix='', location=True, room=True, netbox=True,
            service=False, module=False, location_label='%(id)s (%(description)s)',
            room_label='%(id)s (%(description)s)', netbox_label='%(sysname)s',
            service_label='%(handler)s', module_label='%(module_number)d'):

        self.location = location
        self.room = room
        self.netbox = netbox
        self.service = service
        self.module = module

        self.location_label = location_label
        self.room_label = room_label
        self.netbox_label = netbox_label
        self.service_label = service_label
        self.module_label = module_label

        self.location_set = Location.objects.order_by(('id')).values()
        self.service_set = Service.objects.order_by('handler').values()

        # Quick hack to add the serial to our values.
        netbox_value_args = [f.attname for f in Netbox._meta.fields]
        netbox_value_args.append('device__serial')
        self.netbox_set = Netbox.objects.order_by('sysname').values(*netbox_value_args)

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

        for field in result.keys():
            if self.prefix:
                submit = 'submit_%s_%s' % (self.prefix, field)
                add = 'add_%s_%s' % (self.prefix, field)
                key = '%s_%s' % (self.prefix, field)
            else:
                submit = 'submit_%s' % field
                add = 'add_%s' % field
                key = field

            if field == 'location':
                # Hack to work around noscript XSS protection that triggers on
                # location
                key = key.replace('location', 'loc')

            if getattr(self, field):
                if request.form.has_key(key):
                    result[field] = request.form.getlist(key)
                elif request.form.has_key(add):
                    result[field] = request.form.getlist(add)

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
                    location_name[location['id']] = self.location_label % location
                    locations[''].append((location['id'], location_name[location['id']]))

                if prefix:
                    name = '%s_%s' % (prefix, 'loc')
                else:
                    name = 'loc'

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
                    room_name[room['id']] = self.room_label % room
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
                    netbox_name[netbox['id']] = self.netbox_label % netbox
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
                    name = self.service_label % service
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
                    name = self.module_label % module
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

        return template.render(context).encode('utf-8')
