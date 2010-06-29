# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.generic.list_detail import object_list
from django.views.generic.create_update import update_object

from nav.models.manage import Netbox, Room, Location
from nav.models.service import Service

from nav.web.seeddb.forms import LocationForm
from nav.web.seeddb.utils import render_seeddb_list

def index(request):
    return render_to_response(
        'seeddb/index.html',
        {
            'title': 'Seed Database',
            'navpath': [('Home', '/'), ('Seed DB', None)],
        },
        RequestContext(request)
    )

def netbox_list(request):
    return render_seeddb_list(
        request,
        Netbox.objects.select_related(
            'device', 'type'
        ).order_by('sysname').all(),
        value_list=('room_id', 'ip', 'category_id', 'organization_id', 'read_only', 'read_write', 'type__name', 'device__serial'),
        labels=(
            'Room', 'Sysname', 'IP', 'Category', 'Organization', 'RO',
            'RW', 'Type', 'Serial'
        ),
        edit_url='seeddb-netbox-edit',
        edit_url_attr='sysname',
        extra_context={
            'title': 'Seed IP devices',
            'navpath': [('Home', '/'), ('Seed DB', reverse('seeddb-index')), ('IP devices', None)],
        }
    )

def service_list(request):
    return render_seeddb_list(
        request,
        Service.objects.select_related(
            'netbox'
        ).order_by('netbox__sysname').all(),
        value_list=('netbox__sysname', 'handler', 'version'),
        labels=('Server', 'Handler', 'Version'),
        edit_url='seeddb-service-edit',
        extra_context={
            'title': 'Seed services',
            'navpath': [('Home', '/'), ('Seed DB', reverse('seeddb-index')), ('Services', None)],
        }
    )

def room_list(request):
    return render_seeddb_list(
        request,
        Room.objects.order_by('id').all(),
        value_list=(
            'id', 'location_id', 'description', 'optional_1', 'optional_2',
            'optional_3', 'optional_4'
        ),
        labels=(
            'Room', 'Location', 'Description', 'Optional 1', 'Optional 2',
            'Optional 3', 'Optional 4'
        ),
        edit_url='seeddb-room-edit',
        extra_context={
            'title': 'Seed rooms',
            'navpath': [('Home', '/'), ('Seed DB', reverse('seeddb-index')), ('Rooms', None)],
        }
    )

def location_list(request):
    return render_seeddb_list(
        request,
        Location.objects.order_by('id').all(),
        value_list=('description',),
        labels=('Location', 'Description'),
        edit_url='seeddb-location-edit',
        extra_context={
            'title': 'Seed Locations',
            'navpath': [('Home', '/'), ('Seed DB', reverse('seeddb-index')), ('Locations', None)],
        }
    )
