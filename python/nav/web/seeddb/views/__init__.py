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

from django.shortcuts import render_to_response
from django.template import RequestContext

from nav.web.seeddb.views.list import netbox_list, service_list, room_list
from nav.web.seeddb.views.list import location_list, organization_list
from nav.web.seeddb.views.list import usage_list, netboxtype_list, vendor_list
from nav.web.seeddb.views.list import subcategory_list, cabling_list
from nav.web.seeddb.views.list import patch_list
from nav.web.seeddb.views.move import organization_move, netbox_move, room_move
from nav.web.seeddb.views.delete import netbox_delete, service_delete
from nav.web.seeddb.views.delete import room_delete, location_delete
from nav.web.seeddb.views.delete import organization_delete, usage_delete
from nav.web.seeddb.views.delete import netboxtype_delete, vendor_delete
from nav.web.seeddb.views.delete import subcategory_delete, cabling_delete
from nav.web.seeddb.views.delete import patch_delete 

TITLE_DEFAULT = 'NAV - Seed Database'

def index(request):
    """Index page. Nothing particularly interesting going on."""
    return render_to_response(
        'seeddb/index.html',
        {
            'title': TITLE_DEFAULT,
            'navpath': [('Home', '/'), ('Seed DB', None)],
            'active': {'index': True},
        },
        RequestContext(request)
    )

def not_implemented(*args, **kwargs):
    """Simple method used with the view_switcher.

    Raises "not implemented if called, but the list pages should make sure this
    function is never called.
    """
    raise NotImplementedError()

def view_switcher(request, list_view=None, move_view=None, delete_view=None):
    """Selects appropriate view depending on POST data.
    """
    if request.method == 'POST':
        if 'move' in request.POST:
            return move_view(request)
        elif 'delete' in request.POST:
            return delete_view(request)
    return list_view(request)

def netbox(request):
    return view_switcher(request,
        list_view=netbox_list,
        move_view=netbox_move,
        delete_view=netbox_delete)

def service(request):
    return view_switcher(request,
        list_view=service_list,
        move_view=not_implemented,
        delete_view=service_delete)

def room(request):
    return view_switcher(request,
        list_view=room_list,
        move_view=room_move,
        delete_view=room_delete)

def location(request):
    return view_switcher(request,
        list_view=location_list,
        move_view=not_implemented,
        delete_view=location_delete)

def organization(request):
    return view_switcher(request,
        list_view=organization_list,
        move_view=organization_move,
        delete_view=organization_delete)

def usage(request):
    return view_switcher(request,
        list_view=usage_list,
        move_view=not_implemented,
        delete_view=usage_delete)

def netboxtype(request):
    return view_switcher(request,
        list_view=netboxtype_list,
        move_view=not_implemented,
        delete_view=netboxtype_delete)

def vendor(request):
    return view_switcher(request,
        list_view=vendor_list,
        move_view=not_implemented,
        delete_view=vendor_delete)

def subcategory(request):
    return view_switcher(request,
        list_view=subcategory_list,
        move_view=not_implemented,
        delete_view=subcategory_delete)

def cabling(request):
    return view_switcher(request,
        list_view=cabling_list,
        move_view=not_implemented,
        delete_view=cabling_delete)

def patch(request):
    return view_switcher(request,
        list_view=patch_list,
        move_view=not_implemented,
        delete_view=patch_delete)
