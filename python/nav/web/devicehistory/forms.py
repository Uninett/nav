#
# Copyright (C) 2013 Uninett AS
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
"""Module comment"""

from datetime import date, timedelta
import logging

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Fieldset, Row, Column, Field
from nav.web.devicehistory.utils import get_event_and_alert_types

_logger = logging.getLogger(__name__)


class MyDateInput(forms.DateInput):
    """Set date as type on date input widget"""
    input_type = 'date'

    def __init__(self, attrs=None, format=None):
        if not attrs:
            attrs = {}
        attrs.setdefault("placeholder", "yyyy-mm-dd")
        super(MyDateInput, self).__init__(attrs=attrs, format=format)


class MyDateField(forms.DateField):
    """Set widget with type = date as default widget"""
    widget = MyDateInput


class DeviceHistoryViewFilter(forms.Form):
    """Form for filtering device history results"""

    groupings = [
        ('location', 'Location'),
        ('room', 'Room'),
        ('netbox', 'Netbox'),
        ('device', 'Device serial'),
        ('datetime', 'Date')
    ]
    from_date = MyDateField(required=False)
    to_date = MyDateField(required=False)
    eventtype = forms.ChoiceField(required=False, label='Type')
    group_by = forms.ChoiceField(choices=groupings, initial='netbox',
                                 required=False)

    def __init__(self, *args, **kwargs):
        super(DeviceHistoryViewFilter, self).__init__(*args, **kwargs)
        self.fields['eventtype'].choices = get_event_and_alert_types()
        self.fields['eventtype'].initial = 'all'
        self.fields['from_date'].initial = date.today() - timedelta(days=7)
        self.fields['to_date'].initial = date.today() + timedelta(days=1)

        common_class = 'medium-3'

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Filters',
                Row(
                    Column('from_date', css_class=common_class),
                    Column('to_date', css_class=common_class),
                    Column(Field('eventtype', css_class='select2'),
                           css_class=common_class),
                    Column(Field('group_by', css_class='select2'),
                           css_class=common_class),
                )
            )
        )

    def clean(self):
        """Uses the initial values for empty fields"""
        cleaned_data = super(DeviceHistoryViewFilter, self).clean()
        for field in self.fields.keys():
            if not cleaned_data.get(field) and self.fields[field].initial:
                cleaned_data[field] = self.fields[field].initial
        self.data = cleaned_data
        return cleaned_data
