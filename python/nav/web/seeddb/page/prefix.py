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

from nav.models.manage import Prefix, NetType, Vlan
from nav.django.forms import CIDRField
from nav.bulkparse import PrefixBulkParser
from nav.bulkimport import PrefixImporter

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit
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
    """The PrefixForm inherits the VlanForm and adds a single extra field, the
    net_address from the Prefix model.

    Special handling is introduced in the __init__ and save methods to hand
    off Vlan data to the superclass and add the Vlan as an attribute to the
    resulting Prefix.

    """
    net_address = CIDRField(label="Prefix/mask (CIDR)")
    net_type = forms.ModelChoiceField(
        queryset=NetType.objects.filter(edit=True))

    class Meta:
        model = Vlan

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            self.prefix_instance = instance
            kwargs['instance'] = instance.vlan
        else:
            self.prefix_instance = Prefix()

        super(PrefixForm, self).__init__(*args, **kwargs)

        if instance:
            self.initial['net_address'] = instance.net_address

        self.fields.keyOrder = ['net_address', 'description', 'net_ident',
                                'organization', 'net_type', 'vlan', 'usage']

    def save(self, commit=True):
        vlan = super(PrefixForm, self).save(commit)
        self.prefix_instance.vlan = vlan
        return forms.save_instance(self, self.prefix_instance,
                                   fields=['net_address'])

def prefix_list(request):
    info = PrefixInfo()
    query = Prefix.objects.filter(vlan__net_type__edit=True)
    value_list = (
        'net_address', 'vlan__net_type', 'vlan__organization',
        'vlan__net_ident', 'vlan__usage', 'vlan__description', 'vlan__vlan')
    return render_list(request, query, value_list, 'seeddb-prefix-edit',
        extra_context=info.template_context)

def prefix_edit(request, prefix_id=None):
    info = PrefixInfo()
    return render_edit(request, Prefix, PrefixForm, prefix_id,
        'seeddb-prefix-edit',
        extra_context=info.template_context)

def prefix_bulk(request):
    info = PrefixInfo()
    return render_bulkimport(
        request, PrefixBulkParser, PrefixImporter,
        'seeddb-prefix',
        extra_context=info.template_context)
