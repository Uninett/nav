#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Controllers for tools part of seeddb"""

from django import forms

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.delete import render_delete
from nav.models.profiles import Tool


class ToolInfo(SeeddbInfo):
    """Container object"""
    active = {'tool': True}
    caption = 'Tools'
    tab_template = 'seeddb/tabs_tool.html'
    _title = 'Tool'
    _navpath = [('Tool', reverse_lazy('seeddb-tool'))]
    hide_move = True
    hide_delete = False
    delete_url = reverse_lazy('seeddb-tool')


class ToolForm(forms.ModelForm):
    """Form representing a tool"""
    class Meta:
        model = Tool


def tool(request):
    """Main controller"""
    return view_switcher(request,
                         list_view=tool_list,
                         move_view=not_implemented,
                         delete_view=tool_delete)


def tool_list(request):
    """Display tools as a list"""
    info = ToolInfo()
    query = Tool.objects.all()
    value_list = ('name', 'uri')
    return render_list(request, query, value_list, 'seeddb-tool-edit',
                       extra_context=info.template_context)


def tool_delete(request):
    """Delete tool"""
    info = ToolInfo()
    return render_delete(request, Tool, 'seeddb-tool',
                         whitelist=SEEDDB_EDITABLE_MODELS,
                         extra_context=info.template_context)


def tool_edit(request, tool_id=None):
    """Add or Edit tool"""
    info = ToolInfo()
    return render_edit(request, Tool, ToolForm, tool_id,
                       'seeddb-tool-edit', extra_context=info.template_context)
