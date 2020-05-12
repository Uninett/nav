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

from nav.models.cabling import Cabling
from nav.models.manage import Room
from nav.bulkparse import CablingBulkParser
from nav.bulkimport import CablingImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete

from ..forms import CablingForm


class CablingInfo(SeeddbInfo):
    active = {'cabling': True}
    caption = 'Cabling'
    active_page = 'cabling'
    documentation_url = '/doc/reference/cabling_and_patch.html'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Cabling'
    verbose_name = Cabling._meta.verbose_name
    _navpath = [('Cabling', reverse_lazy('seeddb-cabling'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-cabling')
    delete_url_name = 'seeddb-cabling-delete'
    back_url = reverse_lazy('seeddb-cabling')
    add_url = reverse_lazy('seeddb-cabling-add')
    bulk_url = reverse_lazy('seeddb-cabling-bulk')


def cabling(request):
    return view_switcher(request,
                         list_view=cabling_list,
                         move_view=not_implemented,
                         delete_view=cabling_delete)


def cabling_list(request):
    info = CablingInfo()
    query = Cabling.objects.none()  # Everything is fetched by API
    value_list = ('room', 'jack', 'building', 'target_room', 'category',
                  'description')
    context = info.template_context
    context.update({
        'rooms': Room.objects.all().order_by('id')
    })
    return render_list(request, query, value_list, 'seeddb-cabling-edit',
                       template='seeddb/list_cables.html',
                       extra_context=context)


def cabling_delete(request, object_id=None):
    info = CablingInfo()
    return render_delete(request, Cabling, 'seeddb-cabling',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context,
                         object_id=object_id)


def cabling_edit(request):
    info = CablingInfo()
    cabling_id = request.GET.get('cablingid')
    return render_edit(request, Cabling, CablingForm, cabling_id,
                       'seeddb-cabling-edit',
                       extra_context=info.template_context)


def cabling_bulk(request):
    info = CablingInfo()
    return render_bulkimport(
        request, CablingBulkParser, CablingImporter,
        'seeddb-cabling',
        extra_context=info.template_context)
