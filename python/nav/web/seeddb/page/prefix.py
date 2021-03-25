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
"""
Forms and controllers for the prefix functionality in SeedDB
"""

from django import forms
from django.db import transaction
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from nav.web.message import new_message, Messages

from nav.models.manage import Prefix, NetType, Vlan
from nav.django.forms import CIDRField
from nav.bulkparse import PrefixBulkParser
from nav.bulkimport import PrefixImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.constants import SEEDDB_EDITABLE_MODELS
from nav.web.seeddb.page import view_switcher, not_implemented
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import _get_object
from nav.web.seeddb.utils.bulk import render_bulkimport
from nav.web.seeddb.utils.delete import render_delete


class PrefixInfo(SeeddbInfo):
    """Info-container for prefix"""

    active = {'prefix': True}
    caption = 'Prefix'
    tab_template = 'seeddb/tabs_generic.html'
    _title = 'Prefix'
    verbose_name = Prefix._meta.verbose_name
    _navpath = [('Prefix', reverse_lazy('seeddb-prefix'))]
    delete_url = reverse_lazy('seeddb-prefix')
    delete_url_name = 'seeddb-prefix-delete'
    back_url = reverse_lazy('seeddb-prefix')
    add_url = reverse_lazy('seeddb-prefix-edit')
    bulk_url = reverse_lazy('seeddb-prefix-bulk')
    hide_move = True


class PrefixForm(forms.ModelForm):
    """Modelform for editing a prefix"""

    net_address = CIDRField(label="Prefix/mask (CIDR)")

    class Meta(object):
        model = Prefix
        fields = ('net_address',)


class PrefixVlanForm(forms.ModelForm):
    """Modelform for Vlan with additional fields for editing prefixes"""

    net_type = forms.ModelChoiceField(queryset=NetType.objects.filter(edit=True))

    class Meta(object):
        model = Vlan
        fields = (
            'description',
            'net_ident',
            'vlan',
            'organization',
            'usage',
            'net_type',
        )


def get_prefix_view(request):
    """Select appropriate view based on request POST data"""
    return view_switcher(
        request,
        list_view=prefix_list,
        delete_view=prefix_delete,
        move_view=not_implemented,
    )


def prefix_list(request):
    """Controller for listing prefixes"""
    info = PrefixInfo()
    query = Prefix.objects.filter(vlan__net_type__edit=True)
    value_list = (
        'net_address',
        'vlan__net_type',
        'vlan__organization',
        'vlan__net_ident',
        'vlan__usage',
        'vlan__description',
        'vlan__vlan',
    )
    return render_list(
        request,
        query,
        value_list,
        'seeddb-prefix-edit',
        extra_context=info.template_context,
    )


def prefix_delete(request, object_id=None):
    """Controller for deleting prefixes"""
    info = PrefixInfo()
    return render_delete(
        request,
        Prefix,
        'seeddb-prefix',
        whitelist=SEEDDB_EDITABLE_MODELS,
        extra_context=info.template_context,
        object_id=object_id,
    )


def prefix_bulk(request):
    """Controller for bulk importing prefixes"""
    info = PrefixInfo()
    return render_bulkimport(
        request,
        PrefixBulkParser,
        PrefixImporter,
        'seeddb-prefix',
        extra_context=info.template_context,
    )


@transaction.atomic()
def prefix_edit(request, prefix_id=None):
    """Controller for editing a prefix"""
    info = PrefixInfo()
    prefix, vlan = get_prefix_and_vlan(prefix_id)
    if request.method == 'POST':
        prefix_form = PrefixForm(request.POST, instance=prefix)
        vlan_form = PrefixVlanForm(request.POST, instance=vlan)
        if prefix_form.is_valid() and vlan_form.is_valid():
            vlan = vlan_form.save()
            prefix = prefix_form.save(commit=False)
            prefix.vlan = vlan
            prefix.save()
            msg = "Saved prefix %s" % prefix.net_address
            new_message(request, msg, Messages.SUCCESS)
            return HttpResponseRedirect(
                reverse('seeddb-prefix-edit', args=(prefix.id,))
            )
    else:
        prefix_form = PrefixForm(instance=prefix, initial=request.GET.dict())
        vlan_form = PrefixVlanForm(instance=vlan, initial=request.GET.dict())
    context = info.template_context
    context.update(
        {
            'object': prefix,
            'form': prefix_form,
            'vlan_form': vlan_form,
            'sub_active': prefix and {'edit': True} or {'add': True},
        }
    )
    return render(request, 'seeddb/edit_prefix.html', context)


def get_prefix_and_vlan(prefix_id):
    """Gets the prefix object and vlan object for this prefix id"""
    prefix = _get_object(Prefix, prefix_id, 'pk')
    vlan = prefix.vlan if prefix else None
    return prefix, vlan
