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

from nav.models.manage import Category, Room, Organization, Netbox
from nav.bulkparse import NetboxBulkParser
from nav.bulkimport import NetboxImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
from nav.web.seeddb.utils.delete import render_delete
from nav.web.seeddb.utils.move import move
from nav.web.seeddb.utils.bulk import render_bulkimport

class NetboxFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        Category.objects.order_by('id').all(), required=False)
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)

class NetboxMoveForm(forms.Form):
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)

class NetboxInfo(SeeddbInfo):
    active = {'netbox': True}
    caption = 'IP Devices'
    tab_template = 'seeddb/tabs_netbox.html'
    _title = 'IP Devices'
    _navpath = [('IP Devices', reverse_lazy('seeddb-netbox'))]
    delete_url = reverse_lazy('seeddb-netbox')

def netbox(request):
    return view_switcher(request,
        list_view=netbox_list,
        move_view=netbox_move,
        delete_view=netbox_delete)

def netbox_list(request):
    info = NetboxInfo()
    query = Netbox.objects.all()
    filter_form = NetboxFilterForm(request.GET)
    value_list = (
        'sysname', 'room', 'ip', 'category', 'organization', 'read_only',
        'read_write', 'snmp_version', 'type__name', 'device__serial')
    return render_list(request, query, value_list, 'seeddb-netbox-edit',
        edit_url_attr='pk',
        filter_form=filter_form,
        extra_context=info.template_context)

def netbox_delete(request):
    info = NetboxInfo()
    return render_delete(request, Netbox, 'seeddb-netbox',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context)

def netbox_move(request):
    info = NetboxInfo()
    return move(request, Netbox, NetboxMoveForm, 'seeddb-netbox',
        title_attr='sysname',
        extra_context=info.template_context)

def netbox_bulk(request):
    info = NetboxInfo()
    return render_bulkimport(
            request, NetboxBulkParser, NetboxImporter,
            'seeddb-netbox',
            extra_context=info.template_context)
