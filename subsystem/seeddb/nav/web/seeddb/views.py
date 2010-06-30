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
    qs = Netbox.objects.all()
    value_list = (
        'sysname', 'room', 'ip', 'category', 'organization', 'read_only',
        'read_write', 'type__name', 'device__serial'
    )
    extra = {
        'title': 'Seed IP devices',
        'navpath': [('Home', '/'), ('Seed DB', reverse('seeddb-index')), ('IP devices', None)],
    }

    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-netbox-edit', edit_url_attr='sysname',
        extra_context=extra)

def service_list(request):
    qs = Service.objects.all()
    value_list = ('netbox__sysname', 'handler', 'version')
    extra = {
        'title': 'Seed services',
        'navpath': [('Home', '/'), ('Seed DB', reverse('seeddb-index')), ('Services', None)],
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-service-edit', extra_context=extra)

def room_list(request):
    qs = Room.objects.all()
    value_list = (
        'id', 'location', 'description', 'optional_1', 'optional_2',
        'optional_3', 'optional_4')
    extra = {
        'title': 'Seed rooms',
        'navpath': [('Home', '/'), ('Seed DB', reverse('seeddb-index')), ('Rooms', None)],
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-room-edit', extra_context=extra)

def location_list(request):
    qs = Location.objects.all()
    value_list = ('id', 'description')
    extra = {
        'title': 'Seed Locations',
        'navpath': [('Home', '/'), ('Seed DB', reverse('seeddb-index')), ('Locations', None)],
    }
    return render_seeddb_list(request, qs, value_list,
        edit_url='seeddb-location-edit', extra_context=extra)
