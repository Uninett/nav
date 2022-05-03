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

from nav.models.manage import NetboxType
from nav.bulkparse import NetboxTypeBulkParser
from nav.bulkimport import NetboxTypeImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete

from ..forms import NetboxTypeFilterForm, NetboxTypeForm


class NetboxTypeInfo(SeeddbInfo):
    active = {'type': True}
    caption = 'Types'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Types'
    verbose_name = NetboxType._meta.verbose_name
    _navpath = [('Types', reverse_lazy('seeddb-type'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-type')
    delete_url_name = 'seeddb-type-delete'
    back_url = reverse_lazy('seeddb-type')
    add_url = reverse_lazy('seeddb-type-edit')
    bulk_url = reverse_lazy('seeddb-type-bulk')


def netboxtype(request):
    return view_switcher(
        request,
        list_view=netboxtype_list,
        move_view=not_implemented,
        delete_view=netboxtype_delete,
    )


def netboxtype_list(request):
    info = NetboxTypeInfo()
    query = NetboxType.objects.select_related("vendor").all()
    filter_form = NetboxTypeFilterForm(request.GET)
    value_list = ('name', 'vendor', 'description', 'sysobjectid')
    return render_list(
        request,
        query,
        value_list,
        'seeddb-type-edit',
        filter_form=filter_form,
        extra_context=info.template_context,
    )


def netboxtype_delete(request, object_id=None):
    info = NetboxTypeInfo()
    return render_delete(
        request,
        NetboxType,
        'seeddb-type',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context,
        object_id=object_id,
    )


def netboxtype_edit(request, type_id=None):
    info = NetboxTypeInfo()
    return render_edit(
        request,
        NetboxType,
        NetboxTypeForm,
        type_id,
        'seeddb-type-edit',
        extra_context=info.template_context,
    )


def netboxtype_bulk(request):
    info = NetboxTypeInfo()
    return render_bulkimport(
        request,
        NetboxTypeBulkParser,
        NetboxTypeImporter,
        'seeddb-type',
        extra_context=info.template_context,
    )
