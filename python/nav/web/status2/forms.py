#
# Copyright (C) 2014 UNINETT AS
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
"""Forms for the status page"""
from operator import itemgetter

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import Layout, Row, Column, Field, Submit

from . import STATELESS_THRESHOLD
from nav.models.event import EventType
from nav.models.manage import Organization, Category
from nav.web.crispyforms import NumberField


class StatusPanelForm(forms.Form):
    """Form representing the status panel options for the user"""

    stateless = forms.BooleanField(required=False,
                                   help_text='Show stateless events')
    stateless_threshold = forms.IntegerField(
        required=True,
        initial=STATELESS_THRESHOLD,
        help_text='Hours back in time to look for stateless events')
    on_maintenance = forms.BooleanField(required=False)
    acknowledged = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(StatusPanelForm, self).__init__(*args, **kwargs)

        self.fields['event_type'] = forms.MultipleChoiceField(
            choices=get_event_types(),
            required=False
        )

        self.fields['alert_type'] = forms.MultipleChoiceField(
            choices=get_alert_types(),
            required=False
        )
        self.fields['category'] = forms.MultipleChoiceField(
            choices=get_categories(),
            required=False
        )
        self.fields['organization'] = forms.MultipleChoiceField(
            choices=get_organizations(),
            required=False
        )

        self.fields['not_event_type'] = forms.MultipleChoiceField(
            choices=get_event_types(),
            required=False
        )
        self.fields['not_alert_type'] = forms.MultipleChoiceField(
            choices=get_alert_types(),
            required=False
        )
        self.fields['not_category'] = forms.MultipleChoiceField(
            choices=get_categories(),
            required=False
        )
        self.fields['not_organization'] = forms.MultipleChoiceField(
            choices=get_organizations(),
            required=False
        )

        column_class = 'medium-3'
        self.helper = FormHelper()
        self.helper.form_id = 'status-form'
        self.helper.form_action = ''
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            Row(
                Column(Field('event_type', css_class='select2'),
                       css_class=column_class),
                Column(Field('alert_type', css_class='select2'),
                       css_class=column_class),
                Column(Field('category', css_class='select2'),
                       css_class=column_class),
                Column(Field('organization', css_class='select2'),
                       css_class=column_class),
            ),
            Row(
                Column(Field('not_event_type', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_alert_type', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_category', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_organization', css_class='select2'),
                       css_class=column_class),
            ),
            Row(
                Column('stateless', 'stateless_threshold',
                       css_class=column_class),
                Column('acknowledged', 'on_maintenance',
                       css_class='medium-3 end')
            )

        )

    def clean_stateless_threshold(self):
        field = 'stateless_threshold'
        data = self.cleaned_data[field]
        if not data:
            data = STATELESS_THRESHOLD
        return data


class StatusWidgetForm(StatusPanelForm):

    def __init__(self, *args, **kwargs):
        super(StatusWidgetForm, self).__init__(*args, **kwargs)

        column_class = 'medium-6'
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column(Field('event_type', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_event_type', css_class='select2'),
                       css_class=column_class),
            ),
            Row(
                Column(Field('category', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_category', css_class='select2'),
                       css_class=column_class),
            ),
            Row(
                Column(Field('alert_type', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_alert_type', css_class='select2'),
                       css_class=column_class),
            ),
            Row(
                Column(Field('organization', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_organization', css_class='select2'),
                       css_class=column_class),
            ),
            Row(
                Column('stateless', 'stateless_threshold',
                       css_class=column_class),
                Column('acknowledged', 'on_maintenance',
                       css_class=column_class)
            ),
            Submit('submit', 'Save')
        )


def get_event_types():
    """Get all event types formatted as choices"""
    return [(e.id, e.id) for e in EventType.objects.all().order_by('id')]


def get_alert_types():
    """
    Creates a tuple structure of the alert types grouped by event types
    suitable for the choices of a MultipleChoiceField with optgroups
    [
      (event_type, [(alert_type, alert_type), (alert_type, alert_type)]),
      (event_type, [(alert_type, alert_type), (alert_type, alert_type)])
    ]

    """
    alert_types = {}
    for event_type in EventType.objects.all():
        if event_type.alerttype_set.all().count():
            if event_type.id not in alert_types:
                alert_types[event_type.id] = []
            for alert_type in event_type.alerttype_set.all().order_by('name'):
                alert_types[event_type.id].append(
                    (alert_type.name, alert_type.name))

    return sorted(alert_types.items(), key=itemgetter(0))


def get_categories():
    """Get all categories formatted as choices"""
    return [(c.id, c.id) for c in Category.objects.all()]


def get_organizations():
    """Get all organizations formatted as choices"""
    return [(o.id, o.id) for o in Organization.objects.all()]
