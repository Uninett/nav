#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Field


class MaintenanceTaskForm(forms.Form):
    start_time = forms.DateTimeField(required=True)
    end_time = forms.DateTimeField(required=False)
    no_end_time = forms.BooleanField(initial=False, required=False)
    description = forms.CharField(widget=forms.Textarea, required=True)

    def __init__(self, *args, **kwargs):
        super(MaintenanceTaskForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column(Field('start_time', css_class='datetimepicker'),
                       css_class="medium-6"),
                Column(Field('end_time', css_class='datetimepicker'),
                       css_class="medium-6"),
            ),
            Row(
                Column(css_class='medium-6'),
                Column('no_end_time', css_class="medium-6")
            ),
            'description')

    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form
            # is valid on its own
            return
        end_time = self.cleaned_data['end_time']
        no_end_time = self.cleaned_data['no_end_time']
        if not no_end_time and not end_time:
            raise forms.ValidationError(
                "End time or no end time must be specified")
        return self.cleaned_data


class MaintenanceAddSingleNetbox(forms.Form):
    """A form used for error-checking only; less code than writing
    a custom variable-checker"""
    netboxid = forms.IntegerField(required=True)
