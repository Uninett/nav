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

from django.shortcuts import render

from nav.models.manage import Location
from nav.bulkparse import LocationBulkParser
from nav.bulkimport import LocationImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.forms import LocationForm
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.bulk import render_bulkimport


class LocationInfo(SeeddbInfo):
    active = {'location': True}
    caption = 'Locations'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Locations'
    verbose_name = Location._meta.verbose_name
    _navpath = [('Locations', reverse_lazy('seeddb-location'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-location')
    delete_url_name = 'seeddb-location-delete'
    back_url = reverse_lazy('seeddb-location')
    add_url = reverse_lazy('seeddb-location-edit')
    bulk_url = reverse_lazy('seeddb-location-bulk')
    copy_url_name = 'seeddb-location-copy'


def location(request):
    return view_switcher(
        request,
        list_view=location_list,
        move_view=not_implemented,
        delete_view=location_delete,
    )


def location_list(request):
    info = LocationInfo()
    context = info.template_context
    context.update(
        {
            'roots': Location.objects.filter(parent=None).order_by('id'),
            'edit_url_name': 'seeddb-location-edit',
        }
    )
    return render(request, 'seeddb/list_tree.html', context)


def location_delete(request, object_id=None):
    info = LocationInfo()
    return render_delete(
        request,
        Location,
        'seeddb-location',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context,
        object_id=object_id,
    )


def location_edit(request, location_id=None, action='edit'):
    info = LocationInfo()
    if location_id:
        copy_url = reverse_lazy(
            info.copy_url_name, kwargs={'action': 'copy', 'location_id': location_id}
        )
    else:
        copy_url = None

    _title = 'Use this location as a template for creating a new location'
    extra_context = {
        'copy_url': copy_url,
        'copy_title': _title,
    }
    extra_context.update(info.template_context)
    return render_edit(
        request,
        Location,
        LocationForm,
        location_id,
        'seeddb-location-edit',
        extra_context=extra_context,
        action=action,
    )


def location_bulk(request):
    info = LocationInfo()
    return render_bulkimport(
        request,
        LocationBulkParser,
        LocationImporter,
        'seeddb-location',
        extra_context=info.template_context,
    )
