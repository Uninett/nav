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

from nav.models.manage import Location
from nav.bulkparse import LocationBulkParser
from nav.bulkimport import LocationImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.bulk import render_bulkimport

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            del self.fields['id']

class LocationInfo(SeeddbInfo):
    active = {'location': True}
    caption = 'Locations'
    tab_template = 'seeddb/tabs_location.html'
    _title = 'Locations'
    _navpath = [('Locations', reverse_lazy('seeddb-location'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-location')

def location(request):
    return view_switcher(request,
        list_view=location_list,
        move_view=not_implemented,
        delete_view=location_delete)

def location_list(request):
    info = LocationInfo()
    value_list = ('id', 'description')
    query = Location.objects.all()
    return render_list(request, query, value_list, 'seeddb-location-edit',
        extra_context=info.template_context)

def location_delete(request):
    info = LocationInfo()
    return render_delete(request, Location, 'seeddb-location',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context)

def location_edit(request, location_id=None):
    info = LocationInfo()
    return render_edit(request, Location, LocationForm, location_id,
        'seeddb-location-edit',
        extra_context=info.template_context)

def location_bulk(request):
    info = LocationInfo()
    return render_bulkimport(
        request, LocationBulkParser, LocationImporter,
        'seeddb-location',
        extra_context=info.template_context)
