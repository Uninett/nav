#
# Copyright (C) 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from datetime import date

from django import forms
from nav.web.crispyforms import set_flat_form_attributes, FormRow, FormColumn
from nav.models.fields import INFINITY


class MaintenanceTaskForm(forms.Form):
    start_time = forms.DateTimeField(required=True)
    end_time = forms.DateTimeField(required=False)
    no_end_time = forms.BooleanField(initial=False, required=False)
    description = forms.CharField(widget=forms.Textarea, required=True)

    def __init__(self, *args, **kwargs):
        super(MaintenanceTaskForm, self).__init__(*args, **kwargs)
        self.fields['start_time'].widget.attrs['class'] = 'datetimepicker'
        self.fields['end_time'].widget.attrs['class'] = 'datetimepicker'

        self.attrs = set_flat_form_attributes(
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self['start_time']], css_classes='medium-6'),
                        FormColumn(fields=[self['end_time']], css_classes='medium-6'),
                    ]
                ),
                self['no_end_time'],
                self['description'],
            ]
        )

        # If end_time infinity, check no_end time and disable input
        try:
            task = kwargs.pop('initial')
            if task and (task['end_time'] == INFINITY):
                task['end_time'] = ''
                self.fields['no_end_time'].widget.attrs['checked'] = 'checked'
                self.fields['end_time'].widget.attrs['disabled'] = 'disabled'
        except KeyError:
            pass

    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form
            # is valid on its own
            return
        end_time = self.cleaned_data['end_time']
        no_end_time = self.cleaned_data['no_end_time']
        if not no_end_time and not end_time:
            raise forms.ValidationError("End time or no end time must be specified")
        if end_time and end_time < self.cleaned_data["start_time"]:
            raise forms.ValidationError("End time must be after start time")
        return self.cleaned_data


class MaintenanceAddSingleNetbox(forms.Form):
    """A form used for error-checking only; less code than writing
    a custom variable-checker"""

    netboxid = forms.IntegerField(required=True)


def _get_current_year():
    return date.today().year


def _get_current_month():
    return date.today().month


class MaintenanceCalendarForm(forms.Form):
    """A form used for displaying a maintenance calendar"""

    year = forms.IntegerField(
        initial=_get_current_year, required=True, min_value=2000, max_value=2100
    )
    month = forms.IntegerField(
        initial=_get_current_month, required=True, min_value=1, max_value=12
    )

    @property
    def cleaned_year(self):
        """Returns the cleaned year value if valid, current year otherwise"""
        return self.cleaned_data['year'] if self.is_valid() else _get_current_year()

    @property
    def cleaned_month(self):
        """Returns the cleaned month if valid, current month otherwise"""
        return self.cleaned_data['month'] if self.is_valid() else _get_current_month()

    @property
    def this_month_start(self):
        """Returns the first date of the month represented by this form instance"""
        return date(self.cleaned_year, self.cleaned_month, 1)

    @property
    def next_month_start(self):
        """Returns the first date of the month after the one represented by this form
        instance
        """
        year = self.cleaned_year
        month = self.cleaned_month + 1

        if month > 12:
            year += 1
            month = 1
        return date(year, month, 1)

    @property
    def previous_month_start(self):
        """Returns the first date of the month before the one represented by this form
        instance
        """
        year = self.cleaned_year
        month = self.cleaned_month - 1

        if month < 1:
            year -= 1
            month = 12
        return date(year, month, 1)
