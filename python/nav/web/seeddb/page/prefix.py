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
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from nav.web.message import new_message, Messages

from nav.models.manage import Prefix, NetType, Vlan
from nav.django.forms import CIDRField
from nav.bulkparse import PrefixBulkParser
from nav.bulkimport import PrefixImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit, _get_object
from nav.web.seeddb.utils.bulk import render_bulkimport

class PrefixInfo(SeeddbInfo):
    active = {'prefix': True}
    caption = 'Prefix'
    tab_template = 'seeddb/tabs_prefix.html'
    _title = 'Prefix'
    _navpath = [('Prefix', reverse_lazy('seeddb-prefix'))]
    hide_move = True
    hide_delete = True

class PrefixForm(forms.ModelForm):
    net_address = CIDRField(label="Prefix/mask (CIDR)")
    class Meta:
        model = Prefix
        fields = ('net_address',)

class PrefixVlanForm(forms.ModelForm):
    net_type = forms.ModelChoiceField(
        queryset=NetType.objects.filter(edit=True))
    class Meta:
        model = Vlan
        fields = ('description', 'net_ident', 'vlan', 'organization', 'usage', 'net_type')

def prefix_list(request):
    info = PrefixInfo()
    query = Prefix.objects.filter(vlan__net_type__edit=True)
    value_list = (
        'net_address', 'vlan__net_type', 'vlan__organization',
        'vlan__net_ident', 'vlan__usage', 'vlan__description', 'vlan__vlan')
    return render_list(request, query, value_list, 'seeddb-prefix-edit',
        extra_context=info.template_context)

def prefix_bulk(request):
    info = PrefixInfo()
    return render_bulkimport(
        request, PrefixBulkParser, PrefixImporter,
        'seeddb-prefix',
        extra_context=info.template_context)

@transaction.commit_on_success
def prefix_edit(request, prefix_id=None):
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
            new_message(request._req, msg, Messages.SUCCESS)
            return HttpResponseRedirect(reverse('seeddb-prefix-edit', args=(prefix.id,)))
    else:
        prefix_form = PrefixForm(instance=prefix)
        vlan_form = PrefixVlanForm(instance=vlan)
    context = info.template_context
    context.update({
        'object': prefix,
        'form': prefix_form,
        'vlan_form': vlan_form,
        'sub_active': prefix and {'edit': True} or {'add': True},
    })
    return render_to_response('seeddb/edit_prefix.html',
        context, RequestContext(request))

def get_prefix_and_vlan(prefix_id):
    prefix = _get_object(Prefix, prefix_id, 'pk')
    vlan = prefix and prefix.vlan or None
    return (prefix, vlan)
