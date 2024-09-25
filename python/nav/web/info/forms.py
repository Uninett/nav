# -*- coding: utf-8 -*-
#
# Copyright (C) 2012 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Forms for use in the info subsystem"""
from types import SimpleNamespace

from django import forms


class SearchForm(forms.Form):
    """The searchform used for base searches"""

    query = forms.CharField(max_length=100, label='', required=False)
    hints = SimpleNamespace(
        placeholder='Search',
        method='get',
        form_id='',
        form_action='',
        form_class='search-form',
    )

    def __init__(self, *args, **kwargs):
        self.hints.form_action = kwargs.pop('form_action', '')
        self.hints.placeholder = kwargs.pop('placeholder', 'Search')
        super(SearchForm, self).__init__(*args, **kwargs)
        self.fields['query'].widget = forms.TextInput(
            attrs={'placeholder': self.hints.placeholder}
        )

    def clean_query(self):
        """Remove whitespace from searchterm"""
        return self.cleaned_data['query'].strip()
