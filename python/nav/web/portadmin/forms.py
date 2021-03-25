#
# Copyright (C) 2014 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Forms for PortAdmin"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Submit


class SearchForm(forms.Form):
    """Form for searching for ip-devices and interfaces"""

    query = forms.CharField(
        label='',
        widget=forms.TextInput(
            attrs={'placeholder': 'Search for ip device or interface'}
        ),
    )

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'portadmin-index'
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='medium-9'),
                Column(
                    Submit('submit', 'Search', css_class='postfix'),
                    css_class='medium-3',
                ),
                css_class='collapse',
            )
        )
