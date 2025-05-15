#
# Copyright (C) 2013, 2014 Uninett AS
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

from nav.web.crispyforms import (
    set_flat_form_attributes,
    FormRow,
    FormColumn,
    SubmitField,
)
from django.core.exceptions import MultipleObjectsReturned
from django import forms

from . import L2TraceQuery


class L2TraceForm(forms.Form):
    """Form for l2traceroute search"""

    host_from = forms.CharField(label='From')
    host_to = forms.CharField(label='To', required=False)
    l2tracer = None

    def __init__(self, *args, **kwargs):
        super(L2TraceForm, self).__init__(*args, **kwargs)

        placeholder_text = "Hostname or IP-address"
        self.fields['host_from'].widget.attrs.update({"placeholder": placeholder_text})
        self.fields['host_to'].widget.attrs.update({"placeholder": placeholder_text})

        self.attrs = set_flat_form_attributes(
            form_method='get',
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self['host_from']], css_classes='medium-6'),
                        FormColumn(fields=[self['host_to']], css_classes='medium-6'),
                    ]
                ),
                SubmitField(value='Trace'),
            ],
        )

    def clean(self):
        cleaned_data = super(L2TraceForm, self).clean()

        host_from = cleaned_data.get('host_from')
        host_to = cleaned_data.get('host_to')
        self.l2tracer = L2TraceQuery(host_from, host_to)
        try:
            self.l2tracer.trace()
        except MultipleObjectsReturned:
            msg = "Input was ambiguous, matching multiple hosts"
            raise forms.ValidationError(msg)

        return cleaned_data

    def clean_host_from(self):
        return self.cleaned_data['host_from'].strip()

    def clean_host_to(self):
        return self.cleaned_data['host_to'].strip()
