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

from nav.web.crispyforms import (
    set_flat_form_attributes,
    SubmitField,
    FormRow,
    FormColumn,
)


class SearchForm(forms.Form):
    """The searchform used for base searches"""

    query = forms.CharField(max_length=100, label='', required=False)

    def __init__(
        self, *args, form_action: str = '', placeholder: str = 'Search', **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.attrs = set_flat_form_attributes(
            form_action=form_action,
            form_method='get',
            form_class='search-form',
            form_fields=[
                FormRow(
                    [
                        FormColumn([self['query']], css_classes='medium-9'),
                        FormColumn(
                            [SubmitField(value='Search', css_classes='postfix')],
                            css_classes='medium-3',
                        ),
                    ],
                    css_classes='collapse',
                ),
            ],
        )
        self.fields['query'].widget.attrs.update({"placeholder": placeholder})

    def clean_query(self):
        """Remove whitespace from searchterm"""
        return self.cleaned_data['query'].strip()
