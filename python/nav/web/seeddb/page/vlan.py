# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Uninett AS
# Copyright (C) 2022 Sikt
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

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Fieldset
from nav.web.crispyforms import LabelSubmit

from nav.models.manage import Vlan, NetType, Organization, Usage

from nav.web.seeddb import SeeddbInfo, reverse_lazy
from nav.web.seeddb.utils.list import render_list
from nav.web.seeddb.utils.edit import render_edit


class VlanInfo(SeeddbInfo):
    active = {'vlan': True}
    caption = 'Vlan'
    tab_template = 'seeddb/tabs_vlan.html'
    _title = 'Vlan'
    _navpath = [('Vlan', reverse_lazy('seeddb-vlan'))]
    hide_move = True
    hide_delete = True
    back_url = reverse_lazy('seeddb-vlan')


class VlanFilterForm(forms.Form):
    net_type = forms.ModelChoiceField(
        NetType.objects.order_by('id').all(), required=False
    )
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False
    )
    usage = forms.ModelChoiceField(Usage.objects.order_by('id').all(), required=False)

    def __init__(self, *args, **kwargs):
        super(VlanFilterForm, self).__init__(*args, **kwargs)
        col_class = 'medium-3'
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'GET'
        self.helper.form_class = 'custom'
        self.helper.layout = Layout(
            Fieldset(
                'Filter vlans',
                Row(
                    Column('net_type', css_class=col_class),
                    Column('organization', css_class=col_class),
                    Column('usage', css_class=col_class),
                    Column(
                        LabelSubmit('submit', 'Filter', css_class='postfix'),
                        css_class=col_class,
                    ),
                ),
            )
        )


class VlanForm(forms.ModelForm):
    class Meta(object):
        model = Vlan
        fields = ('vlan', 'organization', 'usage')


def vlan_list(request):
    info = VlanInfo()
    query = (
        Vlan.objects.extra(
            select={
                'prefixes_list': (
                    "array_to_string("
                    "ARRAY(SELECT netaddr FROM prefix "
                    "WHERE vlanid=vlan.vlanid), ', ')"
                )
            }
        )
        .select_related("net_type", "organization", "usage")
        .all()
    )
    filter_form = VlanFilterForm(request.GET)
    value_list = (
        'net_type',
        'vlan',
        'organization',
        'usage',
        'net_ident',
        'description',
        'prefixes_list',
    )
    return render_list(
        request,
        query,
        value_list,
        'seeddb-vlan-edit',
        filter_form=filter_form,
        extra_context=info.template_context,
    )


def vlan_edit(request, vlan_id=None):
    if vlan_id:
        detail_page_url = reverse_lazy('vlan-details', kwargs={'vlanid': vlan_id})
    else:
        detail_page_url = ""
    info = VlanInfo()
    extra_context = {
        'detail_page_url': detail_page_url,
    }
    extra_context.update(info.template_context)
    return render_edit(
        request,
        Vlan,
        VlanForm,
        vlan_id,
        'seeddb-vlan-edit',
        template='seeddb/edit_vlan.html',
        extra_context=extra_context,
    )
