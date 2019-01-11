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

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Submit, Field
from . import L2TraceQuery
from django.core.exceptions import MultipleObjectsReturned


class L2TraceForm(forms.Form):
    """Form for l2traceroute search"""
    host_from = forms.CharField(label='From')
    host_to = forms.CharField(label='To', required=False)
    l2tracer = None

    def __init__(self, *args, **kwargs):
        super(L2TraceForm, self).__init__(*args, **kwargs)

        placeholder_text = "Hostname or IP-address"

        self.helper = FormHelper()
        self.helper.form_action = ""
        self.helper.form_method = 'GET'

        self.helper.layout = Layout(
            Row(
                Column(Field('host_from', placeholder=placeholder_text),
                       css_class='medium-6'),
                Column(Field('host_to', placeholder=placeholder_text),
                       css_class='medium-6'),
            ),
            Submit('submit', 'Trace')
        )

    def clean(self):
        cleaned_data = super(L2TraceForm, self).clean()

        host_from = cleaned_data.get('host_from')
        host_to = cleaned_data.get('host_to')
        self.l2tracer = L2TraceQuery(host_from, host_to)
        try:
            self.l2tracer.trace()
        except MultipleObjectsReturned:
            msg = u"Input was ambiguous, matching multiple hosts"
            raise forms.ValidationError(msg)

        return cleaned_data

    def clean_host_from(self):
        return self.cleaned_data['host_from'].strip()

    def clean_host_to(self):
        return self.cleaned_data['host_to'].strip()
