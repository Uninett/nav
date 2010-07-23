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
    raise Exception, "Not implemented"

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
        delete=not_implemented)

def room(request):
    return list_view(request,
        list=room_list,
        move=room_move,
        delete=not_implemented)

def organization(request):
    return list_view(request,
        list=organization_list,
        move=organization_move,
        delete=not_implemented)
