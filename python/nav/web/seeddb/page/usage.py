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
"""Module containing all things regarding usages in seeddb"""

from django import forms

from nav.models.manage import Usage
from nav.bulkparse import UsageBulkParser
from nav.bulkimport import UsageImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.bulk import render_bulkimport


class UsageInfo(SeeddbInfo):
    """Class for storing meta information related to editing usages"""

    active = {'usage': True}
    caption = 'Usage categories'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Usage categories'
    verbose_name = Usage._meta.verbose_name
    _navpath = [('Usage', reverse_lazy('seeddb-usage'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-usage')
    delete_url_name = 'seeddb-usage-delete'
    back_url = reverse_lazy('seeddb-usage')
    add_url = reverse_lazy('seeddb-usage-edit')
    bulk_url = reverse_lazy('seeddb-usage-bulk')


class UsageForm(forms.ModelForm):
    """Form for editing and creating usages"""

    class Meta(object):
        model = Usage
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(UsageForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            del self.fields['id']


def usage(request):
    """Creates a view switcher containing the appropriate views"""
    return view_switcher(
        request,
        list_view=usage_list,
        move_view=not_implemented,
        delete_view=usage_delete,
    )


def usage_list(request):
    """The view used when listing all usages"""
    info = UsageInfo()
    query = Usage.objects.all()
    value_list = ('id', 'description')
    return render_list(
        request,
        query,
        value_list,
        'seeddb-usage-edit',
        extra_context=info.template_context,
    )


def usage_delete(request, object_id=None):
    """The view used when deleting usages"""
    info = UsageInfo()
    return render_delete(
        request,
        Usage,
        'seeddb-usage',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context,
        object_id=object_id,
    )


def usage_edit(request, usage_id=None):
    """The view used when editing usages"""
    info = UsageInfo()
    return render_edit(
        request,
        Usage,
        UsageForm,
        usage_id,
        'seeddb-usage-edit',
        extra_context=info.template_context,
    )


def usage_bulk(request):
    """The view used when bulk importing usages"""
    info = UsageInfo()
    return render_bulkimport(
        request,
        UsageBulkParser,
        UsageImporter,
        'seeddb-usage',
        extra_context=info.template_context,
    )
