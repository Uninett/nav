#
# Copyright 2011 Uninett AS
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
"""Forms for threshold app"""

import re

from django import forms

from nav.metrics.thresholds import ThresholdEvaluator, InvalidExpressionError
from nav.models.thresholds import ThresholdRule
from nav.util import parse_interval
from nav.web.crispyforms import (
    FlatFieldset,
    SubmitField,
    set_flat_form_attributes,
    FormRow,
    FormColumn,
    HelpFormField,
)


class ThresholdForm(forms.ModelForm):
    """Form for creating a threshold rule"""

    period = forms.CharField(
        max_length=200,
        required=False,
        help_text="The threshold monitor will calculate an average value from "
        "the data points that span this time interval. You should "
        "ensure that the metric has at least two data points in this "
        "interval. For interface counters, the recommended minimum "
        "value is 15 minutes ('15m'). If omitted, the period "
        "defaults to 5 minutes.",
    )

    def __init__(self, *args, **kwargs):
        super(ThresholdForm, self).__init__(*args, **kwargs)
        self.fields['alert'].label = 'Alert threshold'
        self.fields['clear'].label = 'Clear alert'
        self.fields[
            'raw'
        ].help_text = (
            "(Advanced): Do not transform the target according to NAV's own rules"
        )

        if self.instance.pk is None:
            action_text = 'Create rule'
        else:
            action_text = 'Edit rule'

        column_class = 'small-4'
        self.attrs = set_flat_form_attributes(
            form_fields=[
                FlatFieldset(
                    legend=action_text,
                    fields=[
                        self['target'],
                        FormRow(
                            fields=[
                                FormColumn(
                                    fields=[HelpFormField(self['alert'])],
                                    css_classes=column_class,
                                ),
                                FormColumn(
                                    fields=[HelpFormField(self['clear'])],
                                    css_classes=column_class,
                                ),
                                FormColumn(
                                    fields=[HelpFormField(self['period'])],
                                    css_classes=column_class,
                                ),
                            ]
                        ),
                        self['description'],
                        FormRow(
                            fields=[
                                FormColumn(
                                    fields=[
                                        SubmitField(value='Save', css_classes='small')
                                    ],
                                    css_classes='small-6',
                                ),
                                FormColumn(
                                    fields=[HelpFormField(self['raw'])],
                                    css_classes='small-6',
                                ),
                            ]
                        ),
                    ],
                )
            ],
        )

    def clean(self):
        cleaned_data = super(ThresholdForm, self).clean()
        if 'target' not in cleaned_data:
            raise forms.ValidationError('Target is required')

        period = cleaned_data.get('period')
        if not period and is_interface(cleaned_data['target']):
            cleaned_data['period'] = parse_interval('15m')
        return cleaned_data

    def clean_period(self):
        """Verify that period is correctly formatted"""
        period = self.cleaned_data['period']
        if not period:
            return None

        try:
            period = parse_interval(period)
        except ValueError:
            raise forms.ValidationError('Invalid period')

        return period

    def clean_alert(self):
        """Validate that the threshold is correctly formatted"""
        alert = self.cleaned_data['alert']
        validate_expression(alert, self)
        return alert

    def clean_clear(self):
        """Validate that the clear threshold is correctly formatted"""
        clear = self.cleaned_data['clear']
        if not clear:
            return clear
        validate_expression(clear, self)
        return clear

    class Meta(object):
        model = ThresholdRule
        fields = ('target', 'alert', 'clear', 'period', 'description', 'raw')
        widgets = {'description': forms.Textarea()}


def validate_expression(expression, form):
    """Validate the expression"""
    target = form.cleaned_data.get('target', '')
    evaluator = ThresholdEvaluator(target)
    try:
        evaluator.evaluate(expression)
    except InvalidExpressionError:
        raise forms.ValidationError('Invalid threshold expression')


def is_interface(metric):
    """Returns true if this metric is an interface counter"""
    return re.match(r'nav\.devices\..*\.ports\..*', metric)
