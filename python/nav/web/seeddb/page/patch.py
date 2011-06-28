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

from nav.models.cabling import Patch
from nav.bulkparse import PatchBulkParser
from nav.bulkimport import PatchImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete

class PatchInfo(SeeddbInfo):
    active = {'patch': True}
    caption = 'Patch'
    tab_template = 'seeddb/tabs_patch.html'
    _title = 'Patch'
    _navpath = [('Patch', reverse_lazy('seeddb-patch'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-patch')

class PatchForm(forms.ModelForm):
    class Meta:
        model = Patch

def patch(request):
    return view_switcher(request,
        list_view=patch_list,
        move_view=not_implemented,
        delete_view=patch_delete)

def patch_list(request):
    query = Patch.objects.all()
    info = PatchInfo()
    value_list = (
        'interface__netbox__sysname', 'interface__ifname',
        'cabling__room', 'cabling__jack', 'split')
    return render_list(request, query, value_list, 'seeddb-patch-edit',
        extra_context=info.template_context)

def patch_delete(request):
    info = PatchInfo()
    return render_delete(request, Patch, 'seeddb-patch',
        whitelist=SEEDDB_EDITABLE_MODELS, extra_context=info.template_context)

def patch_edit(request, patch_id=None):
    info = PatchInfo()
    return render_edit(request, Patch, PatchForm, patch_id,
        'seeddb-patch-edit',
        extra_context=info.template_context)

def patch_bulk(request):
    info = PatchInfo()
    return render_bulkimport(
        request, PatchBulkParser, PatchImporter,
        'seeddb-patch',
        extra_context=info.template_context)
