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


class ThresholdForm(forms.Form):
    metric = forms.CharField()
    threshold = forms.CharField(help_text='Examples: >95%, >20, <10')
    lower = forms.CharField(label='Lower threshold',
                            help_text='The threshold for cancelling an alert')
    comment = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super(ThresholdForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.layout = Layout(
            Fieldset(
                'Create threshold',
                'metric',
                Row(
                    Column(HelpField('threshold'), css_class='small-6'),
                    Column(HelpField('lower'), css_class='small-6')
                ),
                'comment',
                Submit('submit', 'Create threshold', css_class='small')
            )
        )
