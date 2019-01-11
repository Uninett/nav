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

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Submit, Field


class SearchForm(forms.Form):
    """The searchform used for base searches"""
    query = forms.CharField(max_length=100, label='', required=False)

    def __init__(self, *args, **kwargs):
        self.helper = get_formhelper(kwargs.pop('form_action', ''),
                                     kwargs.pop('placeholder', 'Search'))
        super(SearchForm, self).__init__(*args, **kwargs)

    def clean_query(self):
        """Remove whitespace from searchterm"""
        return self.cleaned_data['query'].strip()


def get_formhelper(form_action, placeholder='Search'):
    """Create a default form layout for a search form"""
    helper = FormHelper()
    helper.form_action = form_action
    helper.form_method = 'GET'
    helper.form_class = 'search-form'
    helper.layout = Layout(
        Row(
            Column(Field('query', placeholder=placeholder),
                   css_class='medium-9'),
            Column(Submit('submit', 'Search', css_class='postfix'),
                   css_class='medium-3'),
            css_class='collapse'
        )
    )
    return helper
