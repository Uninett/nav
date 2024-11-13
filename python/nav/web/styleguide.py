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
"""Renders the styleguide"""

from django.shortcuts import render
from django import forms

from nav.web.crispyforms import (
    FlatFieldset,
    FormColumn,
    FormRow,
    set_flat_form_attributes,
)


class StyleFormOne(forms.Form):
    """Form displaying use of helptext"""

    name = forms.CharField(help_text='Your name')
    address = forms.CharField(help_text='Your address')


class StyleFormTwo(forms.Form):
    """More complex form"""

    name = forms.CharField(help_text='Your name')
    address = forms.CharField(help_text='Your address')

    def __init__(self, *args, **kwargs):
        super(StyleFormTwo, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FlatFieldset(
                    legend="Address form",
                    fields=[
                        FormRow(
                            fields=[
                                FormColumn(
                                    fields=[self["name"]], css_classes="small-6"
                                ),
                                FormColumn(
                                    fields=[self["address"]], css_classes="small-6"
                                ),
                            ]
                        )
                    ],
                )
            ]
        )


def styleguide_index(request):
    """Controller for rendering the styleguide"""
    context = {'form1': StyleFormOne(), 'form2': StyleFormTwo()}

    return render(request, 'styleguide.html', context)
