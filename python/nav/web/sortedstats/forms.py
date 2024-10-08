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

from nav.web.crispyforms import (
    FlatFieldset,
    FormColumn,
    FormRow,
    SubmitField,
    set_flat_form_attributes,
)
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
    choices = [(tf, TIMEFRAMES[tf]['descr']) for tf in TIMEFRAMES]
    timeframe = forms.ChoiceField(choices=choices, initial=choices[1][0])
    rows = NumberField(initial=5)

    use_cache = forms.BooleanField(
        initial=True,
        help_text=(
            "Ticking this box will make it so results "
            "are fetched from a cache if possible. "
            "If the cache is empty, live data is fetched instead."
        ),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super(ViewForm, self).__init__(*args, **kwargs)

        self.attrs = set_flat_form_attributes(
            form_method="get",
            form_class="custom",
            form_fields=[
                FlatFieldset(
                    "Choose statistic",
                    fields=[
                        FormRow(
                            fields=[
                                FormColumn(
                                    fields=[self["view"]], css_classes="medium-5"
                                ),
                                FormColumn(
                                    fields=[self["timeframe"]], css_classes="medium-3"
                                ),
                                FormColumn(
                                    fields=[self["rows"]], css_classes="medium-1"
                                ),
                                FormColumn(
                                    fields=[
                                        SubmitField(
                                            value="Show statistics",
                                            css_classes="postfix",
                                            has_empty_label=True,
                                        )
                                    ],
                                    css_classes="medium-3",
                                ),
                                FormColumn(fields=[self["use_cache"]]),
                            ]
                        )
                    ],
                )
            ],
        )
