#
# Copyright 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Forms for threshold app"""

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (Layout, Fieldset, Submit, Row,
                                            Column)
from nav.web.crispyforms import HelpField
from nav.metrics.thresholds import ThresholdEvaluator, InvalidExpressionError
from nav.models.thresholds import ThresholdRule
from nav.util import parse_interval


class ThresholdForm(forms.ModelForm):
    """Form for creating a threshold rule"""

    def __init__(self, *args, **kwargs):
        super(ThresholdForm, self).__init__(*args, **kwargs)
        if self.instance.pk is None:
            action_text = 'Create threshold'
        else:
            action_text = 'Edit threshold'

        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.layout = Layout(
            Fieldset(
                action_text,
                'target',
                Row(
                    Column(HelpField('alert'), css_class='small-4'),
                    Column(HelpField('clear'), css_class='small-4'),
                    Column(HelpField('period'), css_class='small-4')
                ),
                'description',
                Submit('submit', action_text, css_class='small')
            )
        )

    def clean_period(self):
        """Verify that period is correctly formatted"""
        period = self.cleaned_data['period']
        try:
            parse_interval(period)
        except ValueError:
            raise forms.ValidationError('Invalid period')

        return period

    def clean_alert(self):
        """Validate that the threshold is correctly formatted"""
        alert = self.cleaned_data['alert']
        target = self.cleaned_data['target']
        evaluator = ThresholdEvaluator(target)
        try:
            evaluator.evaluate(alert)
        except InvalidExpressionError:
            raise forms.ValidationError('Invalid threshold expression')

        return alert

    def clean_clear(self):
        """Validate that the threshold is correctly formatted"""
        clear = self.cleaned_data['clear']
        if not clear:
            return clear

        target = self.cleaned_data['target']
        evaluator = ThresholdEvaluator(target)
        try:
            evaluator.evaluate(clear)
        except InvalidExpressionError:
            raise forms.ValidationError('Invalid threshold expression')

        return clear

    class Meta:
        model = ThresholdRule
        fields = ('target', 'alert', 'clear', 'period', 'description')
        widgets = {
            'description': forms.Textarea()
        }
