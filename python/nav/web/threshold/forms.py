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
from nav.models.thresholds import ThresholdRule
from nav.util import parse_interval


class ThresholdForm(forms.ModelForm):
    """Form for creating a threshold rule"""

    def __init__(self, *args, **kwargs):
        super(ThresholdForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.layout = Layout(
            Fieldset(
                'Create threshold',
                'target',
                Row(
                    Column(HelpField('alert'), css_class='small-4'),
                    Column(HelpField('clear'), css_class='small-4'),
                    Column(HelpField('period'), css_class='small-4')
                ),
                'description',
                Submit('submit', 'Create threshold', css_class='small')
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

    class Meta:
        model = ThresholdRule
        fields = ('target', 'alert', 'clear', 'period', 'description')
        widgets = {
            'description': forms.Textarea()
        }
