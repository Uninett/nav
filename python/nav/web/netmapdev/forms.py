# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2012 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from nav.django.forms import MultiSelectFormField
from nav.models.profiles import LINK_TYPES

class NewViewSaveForm(forms.Form):
    title = forms.CharField(label='Title', required=True)
    link_types = MultiSelectFormField(choices=LINK_TYPES,
        label='Link types:', required=True)
    zoom = forms.CharField(max_length=255, label='Zoom', required=True)
    is_public = forms.BooleanField(label='Is public?', initial=False)
    fixed_nodes = forms.CharField(required=False)

    def clean(self):
        if (self._errors):
            return
        return self.cleaned_data

class ViewSaveForm(forms.Form):
    title = forms.CharField(label='Title', required=False)
    link_types = MultiSelectFormField(choices=LINK_TYPES,
        label='Link types:', required=False)
    zoom = forms.CharField(max_length=255, label='Zoom', required=False)
    query = forms.CharField(max_length=100, label='IP or hostname',
        required=False)
    is_public = forms.BooleanField(label='Is public?', required=False)
    fixed_nodes = forms.CharField(required=False)

    def clean(self):
        if (self._errors):
            return
        return self.cleaned_data

