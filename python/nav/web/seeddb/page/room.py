# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 UNINETT AS
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

from django import forms

from nav.models.manage import Location, Room
from nav.bulkparse import RoomBulkParser
from nav.bulkimport import RoomImporter

from nav.web.seeddb import SeeddbInfo
from nav.web.seeddb.page import view_switcher
from nav.web.seeddb.utils.list import render_list

class RoomFilterForm(forms.Form):
    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all(), required=False)

class RoomForm(forms.ModelForm):
    location = forms.ModelChoiceField(
        queryset=Location.objects.order_by('id'))
    class Meta:
        model = Room

class RoomMoveForm(MoveForm):
    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all())

class RoomInfo(SeeddbInfo):
    active = {'room': True},
    caption = 'Rooms'
    tab_template = 'seeddb/tabs_room.html'
    _title = 'Rooms'
    _navpath = [('Rooms', None)]

def room(request):
    return view_switcher(request,
        list_view=room_list,
        move_view=room_move,
        delete_view=room_delete)

def room_list(request):
    info = RoomInfo()
    value_list = (
        'id', 'location', 'description', 'position', 'optional_1',
        'optional_2', 'optional_3', 'optional_4')
    query = Room.objects.all()
    filter_form = RoomFilterForm(request.GET)
    return render_list(request, query, value_list, 'seeddb-room-edit',
        filter_form=filter_form,
        extra_context=info.template_context)

def room_move(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Room', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
        'active': {'room': True},
    }
    return move(request, Room, RoomMoveForm, 'seeddb-room',
        extra_context=extra)

def room_delete(request):
    extra = {
        'navpath': NAVPATH_DEFAULT + [('Room', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
        'active': {'room': True},
    }
    return render_delete(request, Room, 'seeddb-room',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=extra)

def room_edit(request, room_id=None):
    extra = {
        'active': {'room': True},
        'navpath': NAVPATH_DEFAULT + [('Room', reverse('seeddb-room'))],
        'tab_template': 'seeddb/tabs_room.html',
        'delete_url': reverse('seeddb-room'),
    }
    return render_edit(request, Room, RoomForm, room_id,
        'seeddb-room-edit',
        extra_context=extra)

def room_bulk(request):
    extra = {
        'active': {'room': True},
        'title': TITLE_DEFAULT + ' - Room',
        'navpath': NAVPATH_DEFAULT + [('Room', None)],
        'tab_template': 'seeddb/tabs_room.html',
    }
    return render_bulkimport(
        request, RoomBulkParser, RoomImporter,
        'seeddb-room',
        extra_context=extra)
