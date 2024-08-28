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
"""Module containing everything regarding vendors in SeedDB"""

from django import forms
from django.urls import reverse_lazy

from nav.models.manage import Vendor
from nav.bulkparse import VendorBulkParser
from nav.bulkimport import VendorImporter

from nav.web.seeddb import SeeddbInfo
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete


class VendorInfo(SeeddbInfo):
    """Class for storing meta information related to vendors in SeedDB"""

    active = {'vendor': True}
    caption = 'Vendors'
    verbose_name = Vendor._meta.verbose_name
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Vendors'
    _navpath = [('Vendors', reverse_lazy('seeddb-vendor'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-vendor')
    back_url = reverse_lazy('seeddb-vendor')
    add_url = reverse_lazy('seeddb-vendor-edit')
    bulk_url = reverse_lazy('seeddb-vendor-bulk')


class VendorForm(forms.ModelForm):
    """Form for editing and creating vendors"""

    class Meta(object):
        model = Vendor
        fields = '__all__'


def vendor(request):
    """Creates a view switcher containing the appropriate views"""
    return view_switcher(
        request,
        list_view=vendor_list,
        move_view=not_implemented,
        delete_view=vendor_delete,
    )


def vendor_list(request):
    """The view used when listing all vendors"""
    info = VendorInfo()
    query = Vendor.objects.all()
    value_list = ('id',)
    return render_list(
        request, query, value_list, None, extra_context=info.template_context
    )


def vendor_delete(request):
    """The view used when deleting vendors"""
    info = VendorInfo()
    return render_delete(
        request,
        Vendor,
        'seeddb-vendor',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context,
    )


def vendor_edit(request, vendor_id=None):
    """The view used when editing vendors"""
    info = VendorInfo()
    return render_edit(
        request,
        Vendor,
        VendorForm,
        vendor_id,
        'seeddb-vendor',
        extra_context=info.template_context,
    )


def vendor_bulk(request):
    """The view used when bulk importing vendors"""
    info = VendorInfo()
    return render_bulkimport(
        request,
        VendorBulkParser,
        VendorImporter,
        'seeddb-vendor',
        extra_context=info.template_context,
    )
