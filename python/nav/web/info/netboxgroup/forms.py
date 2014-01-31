#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Forms for netbox group info page"""


from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Field, Submit


class NetboxGroupForm(forms.Form):
    """Form for searching for netbox groups"""

    query = forms.CharField(max_length=100, label='')

    def __init__(self, *args, **kwargs):
        super(NetboxGroupForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'netbox-group'
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column(Field('query', placeholder='Device group'),
                       css_class='medium-9'),
                Column(Submit('submit', 'Search', css_class='postfix'),
                       css_class='medium-3'),
                css_class='collapse'
            )
        )

    def clean_query(self):
        """Returns a cleaned version of the searchstring"""
        return self.cleaned_data['query'].strip()
