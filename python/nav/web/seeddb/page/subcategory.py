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

from nav.models.manage import Subcategory, Category
from nav.bulkparse import SubcatBulkParser
from nav.bulkimport import SubcatImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete

class SubcategoryInfo(SeeddbInfo):
    active = {'subcategory': True}
    caption = 'Subcategories'
    tab_template = 'seeddb/tabs_subcategory.html'
    _title = 'Subcategories'
    _navpath = [('Subcategories', reverse_lazy('seeddb-subcategory'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-subcategory')

class SubcategoryFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        Category.objects.order_by('id').all(), required=False)

class SubcategoryForm(forms.ModelForm):
    class Meta:
        model = Subcategory

def subcategory(request):
    return view_switcher(request,
        list_view=subcategory_list,
        move_view=not_implemented,
        delete_view=subcategory_delete)

def subcategory_list(request):
    info = SubcategoryInfo()
    query = Subcategory.objects.all()
    filter_form = SubcategoryFilterForm(request.GET)
    value_list = ('id', 'category', 'description')
    return render_list(request, query, value_list, 'seeddb-subcategory-edit',
        filter_form=filter_form,
        extra_context=info.template_context)

def subcategory_delete(request):
    info = SubcategoryInfo()
    return render_delete(request, Subcategory, 'seeddb-subcategory',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context)

def subcategory_edit(request, subcategory_id=None):
    info = SubcategoryInfo()
    return render_edit(request, Subcategory, SubcategoryForm, subcategory_id,
        'seeddb-subcategory-edit',
        extra_context=info.template_context)

def subcategory_bulk(request):
    info = SubcategoryInfo()
    return render_bulkimport(
        request, SubcatBulkParser, SubcatImporter,
        'seeddb-subcategory',
        extra_context=info.template_context)
