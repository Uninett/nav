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
    active = {'usage': True}
    caption = 'Usage categories'
    tab_template = 'seeddb/tabs_usage.html'
    _title = 'Usage categories'
    _navpath = [('Usage', reverse_lazy('seeddb-usage'))]
    hide_move = True
    delete_url = reverse_lazy('seeddb-usage')

class UsageForm(forms.ModelForm):
    class Meta:
        model = Usage

    def __init__(self, *args, **kwargs):
        super(UsageForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            del self.fields['id']

def usage(request):
    return view_switcher(request,
        list_view=usage_list,
        move_view=not_implemented,
        delete_view=usage_delete)

def usage_list(request):
    info = UsageInfo()
    query = Usage.objects.all()
    value_list = ('id', 'description')
    return render_list(request, query, value_list, 'seeddb-usage-edit',
        extra_context=info.template_context)

def usage_delete(request):
    info = UsageInfo()
    return render_delete(request, Usage, 'seeddb-usage',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context)

def usage_edit(request, usage_id=None):
    info = UsageInfo()
    return render_edit(request, Usage, UsageForm, usage_id,
        'seeddb-usage-edit',
        extra_context=info.template_context)

def usage_bulk(request):
    info = UsageInfo()
    return render_bulkimport(
        request, UsageBulkParser, UsageImporter,
        'seeddb-usage',
        extra_context=info.template_context)
