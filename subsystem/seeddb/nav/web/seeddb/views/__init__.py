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

from nav.web.seeddb.views.list import *
from nav.web.seeddb.views.edit import *
from nav.web.seeddb.views.move import *
from nav.web.seeddb.views.delete import *

TITLE_DEFAULT = 'NAV - Seed Database'

def index(request):
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
    raise NotImplementedError()

def list_view(request, list=None, move=None, delete=None):
    if request.method == 'POST':
        if 'move' in request.POST:
            return move(request)
        elif 'delete' in request.POST:
            return delete(request)
    return list(request)

def netbox(request):
    return list_view(request,
        list=netbox_list,
        move=netbox_move,
        delete=netbox_delete)

def service(request):
    return list_view(request,
        list=service_list,
        move=not_implemented,
        delete=service_delete)

def room(request):
    return list_view(request,
        list=room_list,
        move=room_move,
        delete=room_delete)

def location(request):
    return list_view(request,
        list=location_list,
        move=not_implemented,
        delete=location_delete)

def organization(request):
    return list_view(request,
        list=organization_list,
        move=organization_move,
        delete=organization_delete)

def usage(request):
    return list_view(request,
        list=usage_list,
        move=not_implemented,
        delete=usage_delete)

def netboxtype(request):
    return list_view(request,
        list=netboxtype_list,
        move=not_implemented,
        delete=netboxtype_delete)

def vendor(request):
    return list_view(request,
        list=vendor_list,
        move=not_implemented,
        delete=vendor_delete)

def subcategory(request):
    return list_view(request,
        list=subcategory_list,
        move=not_implemented,
        delete=subcategory_delete)

def cabling(request):
    return list_view(request,
        list=cabling_list,
        move=not_implemented,
        delete=cabling_delete)

def patch(request):
    return list_view(request,
        list=patch_list,
        move=not_implemented,
        delete=patch_delete)
