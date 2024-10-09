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
from nav.web.crispyforms import (
    set_flat_form_attributes,
    SubmitField,
    FormRow,
    FormColumn,
)


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
        self.attrs = set_flat_form_attributes(
            form_method='get',
            form_action='portadmin-index',
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self['query']], css_classes='medium-9'),
                        FormColumn(
                            fields=[SubmitField(value='Search', css_classes='postfix')],
                            css_classes='medium-3',
                        ),
                    ],
                    css_classes='collapse',
                )
            ],
        )
