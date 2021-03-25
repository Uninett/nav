#
# Copyright (C) 2014 Uninett AS
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
"""Forms for sorted stats"""

from operator import itemgetter
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Fieldset, Row, Column
from nav.web.crispyforms import LabelSubmit
from . import CLASSMAP, TIMEFRAMES


def get_sections_list():
    """Return sections list usable in form choices"""
    return sorted([(x[0], x[1].title) for x in CLASSMAP.items()], key=itemgetter(0))


class NumberInput(forms.TextInput):
    """Input widget with type set to number"""

    input_type = 'number'


class NumberField(forms.IntegerField):
    """Input field with type set to number"""

    widget = NumberInput


class ViewForm(forms.Form):
    """Form the choosing which view to see on the statistics page"""

    view = forms.ChoiceField(choices=get_sections_list())
    timeframe = forms.ChoiceField(choices=TIMEFRAMES, initial=TIMEFRAMES[1][0])
    rows = NumberField(initial=5)

    def __init__(self, *args, **kwargs):
        super(ViewForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'custom'
        self.helper.form_action = ''
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Fieldset(
                'Choose statistic',
                Row(
                    Column('view', css_class='medium-5'),
                    Column('timeframe', css_class='medium-3'),
                    Column('rows', css_class='medium-1'),
                    Column(
                        LabelSubmit('submit', 'Show statistics', css_class='postfix'),
                        css_class='medium-3',
                    ),
                ),
            )
        )
