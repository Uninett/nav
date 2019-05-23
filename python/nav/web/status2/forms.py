#
# Copyright (C) 2014, 2015 Uninett AS
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
"""Forms for the status page"""
from collections import defaultdict
from operator import itemgetter

from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (Layout, Row, Column, Field, Submit,
                                            HTML, Fieldset)

from nav.models.event import EventType, AlertType
from nav.models.manage import Organization, Category, NetboxGroup, Location
from nav.web.crispyforms import NumberField
from . import STATELESS_THRESHOLD


class StatusPanelForm(forms.Form):
    """Form representing the status panel options for the user"""

    stateless = forms.BooleanField(required=False,
                                   help_text='Show stateless events')
    stateless_threshold = NumberField(
        required=True,
        initial=STATELESS_THRESHOLD,
        help_text='Hours back in time to look for stateless events')
    on_maintenance = forms.BooleanField(required=False)
    acknowledged = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(StatusPanelForm, self).__init__(*args, **kwargs)

        alert_types = get_alert_types()

        self.fields['event_type'] = forms.MultipleChoiceField(
            choices=get_event_types(),
            required=False
        )

        self.fields['alert_type'] = forms.MultipleChoiceField(
            choices=alert_types,
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
        self.fields['device_group'] = forms.MultipleChoiceField(
            choices=get_device_groups(),
            required=False
        )

        self.fields['location'] = forms.MultipleChoiceField(
            choices=get_locations(),
            required=False
        )

        self.fields['not_event_type'] = forms.MultipleChoiceField(
            choices=get_event_types(),
            required=False
        )
        self.fields['not_alert_type'] = forms.MultipleChoiceField(
            choices=alert_types,
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
        self.fields['not_device_group'] = forms.MultipleChoiceField(
            choices=get_device_groups(),
            required=False
        )
        self.fields['not_location'] = forms.MultipleChoiceField(
            choices=get_locations(),
            required=False
        )

        self.fields['status_filters'] = forms.MultipleChoiceField(
            choices=[(t, forms.forms.pretty_name(t))
                     for t, f in self.fields.items()
                     if isinstance(f, forms.MultipleChoiceField)],
            required=False,
            label='Choose fields to filter status by'
        )

        column_class = 'medium-6'
        self.helper = FormHelper()
        self.helper.form_id = 'status-form'
        self.helper.form_action = ''
        self.helper.form_method = 'POST'
        self.helper.layout = Layout(
            Row(
                Column(
                    Field('status_filters', css_class='select2'),
                    Fieldset(
                        'Status filters',
                        Field('alert_type', css_class='select2'),
                        Field('category', css_class='select2'),
                        Field('device_group', css_class='select2'),
                        Field('event_type', css_class='select2'),
                        Field('location', css_class='select2'),
                        Field('organization', css_class='select2'),
                        Field('not_alert_type', css_class='select2'),
                        Field('not_category', css_class='select2'),
                        Field('not_device_group', css_class='select2'),
                        Field('not_event_type', css_class='select2'),
                        Field('not_location', css_class='select2'),
                        Field('not_organization', css_class='select2'),
                        css_class='field_list'),
                    css_class=column_class),
                Column('stateless', 'stateless_threshold',
                       'acknowledged', 'on_maintenance',
                       css_class=column_class),
            ),
            HTML('<hr>'),

        )

    def clean_stateless_threshold(self):
        """Set default stateless threshold"""
        field = 'stateless_threshold'
        data = self.cleaned_data[field]
        if not data:
            data = STATELESS_THRESHOLD
        return data


class StatusWidgetForm(StatusPanelForm):
    """
    This form is used in the status widget and is more suitable for a smaller
    screen size.
    """
    extra_columns = forms.MultipleChoiceField(
        required=False,
        choices=(('room.location', 'Location'), ('room', 'Room'),
                 ('organization', 'Organization'))
    )

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
                Column(Field('device_group', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_device_group', css_class='select2'),
                       css_class=column_class),
            ),
            Row(
                Column(Field('location', css_class='select2'),
                       css_class=column_class),
                Column(Field('not_location', css_class='select2'),
                       css_class=column_class),
            ),
            Row(
                Column('stateless', 'stateless_threshold',
                       css_class=column_class),
                Column('acknowledged', 'on_maintenance', 'extra_columns',
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
    alert_types = defaultdict(list)
    for alert_type in AlertType.objects.all():
        alert_types[alert_type.event_type_id].append(
            (alert_type.name, alert_type.name))

    return sorted(alert_types.items(), key=itemgetter(0))


def get_categories():
    """Get all categories formatted as choices"""
    return [(c.id, c.id) for c in Category.objects.all()]


def get_organizations():
    """Get all organizations formatted as choices"""
    return [(o.id, o.id) for o in Organization.objects.all()]


def get_device_groups():
    """Get all device groups formatted as choices"""
    return [(n.id, n.id) for n in NetboxGroup.objects.all()]


def get_locations():
    """Gets all locations formatted as choices"""
    return [(l.id, l.id) for l in Location.objects.all()]
