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
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Field, Submit
from nav.web.crispyforms import LabelSubmit


class SearchForm(forms.Form):
    """Form for searching for ip devices in info"""
    query = forms.CharField(max_length=100, label='')

    def __init__(self, *args, **kwargs):
        super(SearchForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = 'ipdevinfo-search'
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column(Field('query', placeholder='IP or hostname'),
                       css_class='medium-9'),
                Column(Submit('submit', 'Search', css_class='postfix'),
                       css_class='medium-3'),
                css_class='collapse'
            )
        )


class ActivityIntervalForm(forms.Form):
    """Form for setting an interval in switch port activity"""
    interval = forms.IntegerField(label='Days', min_value=0)

    def __init__(self, *args, **kwargs):
        super(ActivityIntervalForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('interval', css_class='small-4'),
                Column(LabelSubmit('submit', 'Recheck activity',
                                   css_class='postfix'),
                       css_class='small-8'),
                css_class='collapse'
            )
        )


class SensorRangesForm(forms.Form):
    """Form for setting display ranges for a sensor"""
    minimum = forms.FloatField(label='Minimum', required=False)
    maximum = forms.FloatField(label='Maximum', required=False)
