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

from nav.models.manage import Vendor
from nav.bulkparse import VendorBulkParser
from nav.bulkimport import VendorImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete

class VendorInfo(SeeddbInfo):
    active = {'vendor': True}
    caption = 'Vendors'
    tab_template = 'seeddb/tabs_vendor.html'
    _title = 'Vendors'
    _navpath = [('Vendors', reverse_lazy('seeddb-vendor'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-vendor')

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor

def vendor(request):
    return view_switcher(request,
        list_view=vendor_list,
        move_view=not_implemented,
        delete_view=vendor_delete)

def vendor_list(request):
    info = VendorInfo()
    query = Vendor.objects.all()
    value_list = ('id',)
    return render_list(request, query, value_list, None,
        extra_context=info.template_context)

def vendor_delete(request):
    info = VendorInfo()
    return render_delete(request, Vendor, 'seeddb-vendor',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context)

def vendor_edit(request, vendor_id=None):
    info = VendorInfo()
    return render_edit(request, Vendor, VendorForm, vendor_id,
        'seeddb-vendor',
        extra_context=info.template_context)

def vendor_bulk(request):
    info = VendorInfo()
    return render_bulkimport(
        request, VendorBulkParser, VendorImporter,
        'seeddb-vendor',
        extra_context=info.template_context)
