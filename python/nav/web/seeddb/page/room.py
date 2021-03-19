# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Forms and view functions for SeedDB's Room view"""

from django.urls import reverse

from nav.models.manage import Room
from nav.bulkparse import RoomBulkParser
from nav.bulkimport import RoomImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.move import move
from nav.web.seeddb.utils.bulk import render_bulkimport

from ..forms import RoomForm, RoomFilterForm, RoomMoveForm


class RoomInfo(SeeddbInfo):
    """Room info object"""

    active = {'room': True}
    caption = 'Rooms'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Rooms'
    verbose_name = Room._meta.verbose_name
    _navpath = [('Rooms', reverse_lazy('seeddb-room'))]
    delete_url = reverse_lazy('seeddb-room')
    delete_url_name = 'seeddb-room-delete'
    back_url = reverse_lazy('seeddb-room')
    add_url = reverse_lazy('seeddb-room-edit')
    bulk_url = reverse_lazy('seeddb-room-bulk')
    copy_url_name = 'seeddb-room-copy'


def room(request):
    """Controller for listing, moving and deleting rooms"""
    return view_switcher(
        request, list_view=room_list, move_view=room_move, delete_view=room_delete
    )


def room_list(request):
    """Controller for listing rooms. Used in room()"""
    info = RoomInfo()
    value_list = ('id', 'location', 'description', 'position', 'data')
    query = Room.objects.all()
    filter_form = RoomFilterForm(request.GET)
    return render_list(
        request,
        query,
        value_list,
        'seeddb-room-edit',
        filter_form=filter_form,
        extra_context=info.template_context,
    )


def room_move(request):
    """Controller for moving rooms. Used in room()"""
    info = RoomInfo()
    return move(
        request, Room, RoomMoveForm, 'seeddb-room', extra_context=info.template_context
    )


def room_delete(request, object_id=None):
    """Controller for deleting rooms. Used in room()"""
    info = RoomInfo()
    return render_delete(
        request,
        Room,
        'seeddb-room',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context,
        object_id=object_id,
    )


def room_edit(request, action='edit', room_id=None, lat=None, lon=None):
    """Controller for editing a room"""
    info = RoomInfo()
    if room_id:
        copy_url = reverse_lazy(
            info.copy_url_name, kwargs={'action': 'copy', 'room_id': room_id}
        )
    else:
        copy_url = None
    roompositions = [
        [float(r.position[0]), float(r.position[1])]
        for r in Room.objects.all()
        if r.position
    ]
    extra_context = {
        'map': True,
        'roompositions': roompositions,
        'copy_url': copy_url,
        'copy_title': 'Use this room as a template for creating a new room',
    }

    extra_context.update(info.template_context)
    return render_edit(
        request,
        Room,
        RoomForm,
        room_id,
        'seeddb-room-edit',
        lon=lon,
        lat=lat,
        extra_context=extra_context,
        action=action,
    )


def room_bulk(request):
    """Controller for bulk editing rooms"""
    info = RoomInfo()
    return render_bulkimport(
        request,
        RoomBulkParser,
        RoomImporter,
        'seeddb-room',
        extra_context=info.template_context,
    )
