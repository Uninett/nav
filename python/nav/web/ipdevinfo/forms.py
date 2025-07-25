# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2008 Uninett AS
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

from django import forms

from nav.models.manage import Sensor
from nav.web.crispyforms import (
    FormColumn,
    FormRow,
    SubmitField,
    set_flat_form_attributes,
)
from ..utils import validate_timedelta_for_overflow


class SearchForm(forms.Form):
    """Form for searching for ip devices in info"""

    query = forms.CharField(max_length=100, label='')

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_action="ipdevinfo-search",
            form_method="get",
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self["query"]], css_classes="medium-9"),
                        FormColumn(
                            fields=[SubmitField(value="Search", css_classes="postfix")],
                            css_classes="medium-3",
                        ),
                    ],
                    css_classes="collapse",
                )
            ],
        )
        self.fields['query'].widget.attrs.update({"placeholder": "IP or hostname"})


class ActivityIntervalForm(forms.Form):
    """Form for setting an interval in switch port activity"""

    interval = forms.IntegerField(label='Days', min_value=0)

    def __init__(self, *args, **kwargs):
        super(ActivityIntervalForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self["interval"]], css_classes="small-4"),
                        FormColumn(
                            fields=[
                                SubmitField(
                                    value="Recheck activity",
                                    css_classes="postfix",
                                    has_empty_label=True,
                                )
                            ],
                            css_classes="small-8",
                        ),
                    ],
                    css_classes="collapse",
                )
            ]
        )

    def clean_interval(self):
        interval = self.cleaned_data["interval"]
        validate_timedelta_for_overflow(days=interval)
        return interval


class SensorRangesForm(forms.Form):
    """Form for setting display ranges for a sensor"""

    minimum = forms.FloatField(label='Minimum', required=False)
    maximum = forms.FloatField(label='Maximum', required=False)

    def __init__(self, *args, **kwargs):
        super(SensorRangesForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_method="post",
            submit_field=SubmitField(value="Update range", css_classes='small'),
        )


class BooleanSensorForm(forms.Form):
    """Form for configuring boolean sensor display"""

    on_message = forms.CharField(
        label='Message when alert is active', initial='The alert is active'
    )
    off_message = forms.CharField(
        label='Message when alert is inactive (ok)', initial='No alert'
    )
    on_state = forms.ChoiceField(
        label='When is the alert considered "on"',
        choices=(('1', 'When the value is 1'), ('0', 'When the value is 0 (zero)')),
    )
    alert_type = forms.ChoiceField(
        label='What to display in "on" state', choices=Sensor.ALERT_TYPE_CHOICES
    )

    def __init__(self, *args, **kwargs):
        super(BooleanSensorForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_method="post",
            submit_field=SubmitField(value="Update settings", css_classes='small'),
        )
