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

from nav.models.cabling import Cabling, Room
from nav.bulkparse import CablingBulkParser
from nav.bulkimport import CablingImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete

class CablingInfo(SeeddbInfo):
    active = {'cabling': True}
    caption = 'Cabling'
    tab_template = 'seeddb/tabs_cabling.html'
    _title = 'Cabling'
    _navpath = [('Cabling', reverse_lazy('seeddb-cabling'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-cabling')

class CablingFilterForm(forms.Form):
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)

class CablingForm(forms.ModelForm):
    class Meta:
        model = Cabling

def cabling(request):
    return view_switcher(request,
        list_view=cabling_list,
        move_view=not_implemented,
        delete_view=cabling_delete)

def cabling_list(request):
    info = CablingInfo()
    query = Cabling.objects.all()
    filter_form = CablingFilterForm(request.GET)
    value_list = (
        'room', 'jack', 'building', 'target_room', 'category', 'description')
    return render_list(request, query, value_list, 'seeddb-cabling-edit',
        filter_form=filter_form,
        extra_context=info.template_context)

def cabling_delete(request):
    info = CablingInfo()
    return render_delete(request, Cabling, 'seeddb-cabling',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context)

def cabling_edit(request, cabling_id=None):
    info = CablingInfo()
    return render_edit(request, Cabling, CablingForm, cabling_id,
        'seeddb-cabling-edit',
        extra_context=info.template_context)

def cabling_bulk(request):
    info = CablingInfo()
    return render_bulkimport(
        request, CablingBulkParser, CablingImporter,
        'seeddb-cabling',
        extra_context=info.template_context)
