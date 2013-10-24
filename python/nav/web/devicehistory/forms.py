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
"""Module comment"""

import time
from datetime import date
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Fieldset, Row, Column
from nav.web.devicehistory.utils import get_event_and_alert_types

# Often used timelimits, in seconds:
ONE_DAY = 24 * 3600
ONE_WEEK = 7 * ONE_DAY


class MyDateInput(forms.DateInput):
    """Set date as type on date input widget"""
    input_type = 'date'


class DeviceHistoryViewFilter(forms.Form):
    """Form for filtering device history results"""

    eventtypes = get_event_and_alert_types()
    groupings = [
        ('location', 'Location'),
        ('room', 'Room'),
        ('netbox', 'Netbox'),
        ('device', 'Device serial'),
        ('datetime', 'Date')
    ]
    from_date = forms.DateField(
        initial=date.fromtimestamp(time.time() - ONE_WEEK), required=False,
        widget=MyDateInput)
    to_date = forms.DateField(
        initial=date.fromtimestamp(time.time() + ONE_DAY), required=False,
        widget=MyDateInput)
    eventtype = forms.ChoiceField(choices=eventtypes, initial='all',
                                  required=False, label='Type')
    group_by = forms.ChoiceField(choices=groupings, initial='netbox',
                                 required=False)

    def __init__(self, *args, **kwargs):
        super(DeviceHistoryViewFilter, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Filters',
                Row(
                    Column('from_date', css_class='medium-3'),
                    Column('to_date', css_class='medium-3'),
                    Column('eventtype', css_class='medium-3'),
                    Column('group_by', css_class='medium-3'),
                )
            )
        )
