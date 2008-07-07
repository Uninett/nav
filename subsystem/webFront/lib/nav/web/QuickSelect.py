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
    def __init__(self, request=None, prefix='', location=True, room=True, netbox=True, service=False, module=False):
        if location:
            self.location = Location.objects.values()
        else:
            self.location = []

        if room:
            self.room = Room.objects.values()
        else:
            self.room = []

        if netbox:
            self.netbox = Netbox.objects.values()
        else:
            self.netbox = []

        if service:
            self.service = Service.objects.values()
        else:
            self.service = []

        if module:
            self.module = Module.objects.values()
        else:
            self.module = []

        self.request = request
        self.prefix = prefix
        self.output = []

    def __str__(self):
        if not self.output:
            prefix = self.prefix
            output = []
            location_name = {}
            room_name = {}
            netbox_name = {}

            if self.location:
                locations = {'': []}
                for location in Location.objects.values():
                    location_name[location['id']] = '%(id)s (%(description)s)' % location
                    locations[''].append((location['id'], location_name[location['id']]))

                [value.sort(key=lambda (k,v): (v,k)) for key,value in locations.iteritems()]

                output.append({
                        'label': 'Location',
                        'name': '_'.join([prefix,'location']),
                        'collapse': True,
                        'objects': sorted(locations.iteritems()),
                    })

            if self.room:
                rooms = {}
                for room in Room.objects.values():
                    location = location_name.get(room['location_id'])
                    room_name[room['id']] = '%(id)s (%(description)s)' % room
                    if location in rooms:
                        rooms[location].append((room['id'], room_name[room['id']]))
                    else:
                        rooms[location] = [(room['id'], room_name[room['id']])]

                [value.sort(key=lambda (k,v): (v,k)) for key,value in rooms.iteritems()]

                output.append({
                        'label': 'Room',
                        'name': '_'.join([prefix,'room']),
                        'collapse': True,
                        'objects': sorted(rooms.iteritems()),
                    })

            if self.netbox:
                netboxes = {}
                for netbox in Netbox.objects.values():
                    room = room_name.get(netbox['room_id'])
                    netbox_name[netbox['id']] = '%(sysname)s' % netbox
                    if room in netboxes:
                        netboxes[room].append((netbox['id'], netbox_name[netbox['id']]))
                    else:
                        netboxes[room] = [(netbox['id'], netbox_name[netbox['id']])]

                [value.sort(key=lambda (k,v): (v,k)) for key,value in netboxes.iteritems()]

                output.append({
                        'label': 'IP device',
                        'name': '_'.join([prefix,'netbox']),
                        'objects': sorted(netboxes.iteritems()),
                    })

            if self.service:
                services = {}
                for service in Service.objects.values():
                    netbox = netbox_name[service['netbox_id']]
                    name = '%(handler)s' % service
                    if netbox in services:
                        services[netbox].append((service['id'], name))
                    else:
                        services[netbox] = [(service['id'], name)]

                [value.sort(key=lambda (k,v): (v,k)) for key,value in services.iteritems()]

                output.append({
                        'label': 'Service',
                        'name': '_'.join([prefix,'service']),
                        'collapse': True,
                        'objects': sorted(services.iteritems()),
                    })

            if self.module:
                modules = {}
                for module in Module.objects.values():
                    netbox = netbox_name[module['netbox_id']]
                    name = '%(module_number)s' % module
                    if netbox in modules:
                        modules[netbox].append((module['id'], name))
                    else:
                        modules[netbox] = [(module['id'], name)]

                [value.sort(key=lambda (k,v): (v,k)) for key,value in modules.iteritems()]

                output.append({
                        'label': 'Module',
                        'name': '_'.join([prefix,'module']),
                        'collapse': True,
                        'objects': sorted(modules.iteritems()),
                    })
            self.output = output


        template = get_template('webfront/quickselect.html')
        context  = Context({'output': output})

        return template.render(context)
