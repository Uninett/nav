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
from nav.web.crispyforms import (
    set_flat_form_attributes,
    FlatFieldset,
    FormRow,
    FormColumn,
)
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
        ('datetime', 'Date'),
    ]
    from_date = MyDateField(required=False)
    to_date = MyDateField(required=False)
    eventtype = forms.ChoiceField(required=False, label='Type')
    eventtype.widget.attrs.update({"class": "select2"})
    group_by = forms.ChoiceField(choices=groupings, initial='netbox', required=False)
    group_by.widget.attrs.update({"class": "select2"})

    @staticmethod
    def get_initial():
        return {
            'eventtype': 'all',
            'from_date': date.today() - timedelta(days=7),
            'to_date': date.today() + timedelta(days=1),
        }

    def __init__(self, *args, **kwargs):
        super(DeviceHistoryViewFilter, self).__init__(*args, **kwargs)
        self.fields['eventtype'].choices = get_event_and_alert_types()
        self.initial = self.get_initial()

        common_class = 'medium-3'

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FlatFieldset(
                    "Filters",
                    fields=[
                        FormRow(
                            fields=[
                                FormColumn(
                                    fields=[self['from_date']], css_classes=common_class
                                ),
                                FormColumn(
                                    fields=[self['to_date']], css_classes=common_class
                                ),
                                FormColumn(
                                    fields=[self['eventtype']], css_classes=common_class
                                ),
                                FormColumn(
                                    fields=[self['group_by']], css_classes=common_class
                                ),
                            ]
                        )
                    ],
                )
            ]
        )

    def clean(self):
        """Uses the initial values for empty fields"""
        cleaned_data = super(DeviceHistoryViewFilter, self).clean()
        for field in self.fields.keys():
            if not cleaned_data.get(field) and self.fields[field].initial:
                cleaned_data[field] = self.fields[field].initial
        self.data = cleaned_data
        return cleaned_data
