# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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

from nav.models.manage import Room, Location, Organization, Usage, Vendor
from nav.models.manage import Category, NetType

class NetboxFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        Category.objects.order_by('id').all(), required=False)
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)

class RoomFilterForm(forms.Form):
    location = forms.ModelChoiceField(
        Location.objects.order_by('id').all(), required=False)

class OrganizationFilterForm(forms.Form):
    parent = forms.ModelChoiceField(
        Organization.objects.filter(
            pk__in=Organization.objects.filter(
                parent__isnull=False
            ).values_list('parent', flat=True)
        ).order_by('id'), required=False)

class NetboxTypeFilterForm(forms.Form):
    vendor = forms.ModelChoiceField(
        Vendor.objects.order_by('id').all(), required=False)

class SubcategoryFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        Category.objects.order_by('id').all(), required=False)

class VlanFilterForm(forms.Form):
    net_type = forms.ModelChoiceField(
        NetType.objects.order_by('id').all(), required=False)
    organization = forms.ModelChoiceField(
        Organization.objects.order_by('id').all(), required=False)
    usage = forms.ModelChoiceField(
        Usage.objects.order_by('id').all(), required=False)

class CablingFilterForm(forms.Form):
    room = forms.ModelChoiceField(
        Room.objects.order_by('id').all(), required=False)
