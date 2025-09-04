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
"""Forms for the radius tool"""

from datetime import datetime

from django import forms
from django.core.validators import validate_ipv4_address
from django.core.validators import validate_integer as django_validate_integer

from nav.web.crispyforms import (
    set_flat_form_attributes,
    FormColumn,
    FormRow,
    SubmitField,
)

from nav.util import is_valid_cidr

from ..utils import validate_timedelta_for_overflow


def validate_integer(value):
    """Validator for integer"""
    try:
        django_validate_integer(value)
    except forms.ValidationError:
        raise forms.ValidationError('Must be a number!')


def validate_cidr(value):
    """Validator for cidr xxx.xxx.xxx.xxx/xx"""
    if not value or not is_valid_cidr(value):
        raise forms.ValidationError('Must be a valid CIDR address!')


def validate_datetime_with_slack(value):
    """Validates a timestamp with or without slack"""
    try:
        values = value.split('|')
        time = values[0]
        slack = 0
        if len(values) > 1:
            slack = values[1]
        datetime.strptime(time, '%Y-%m-%d %H:%M')
        int(slack)
    except (ValueError, TypeError):
        raise forms.ValidationError('Must be of this format YYYY-MM-DD hh:mm|slack')


class MultitypeQueryWidget(forms.MultiWidget):
    """
    Widget for MultitypeQueryField
    """

    def decompress(self, value):
        return [value]

    def format_output(self, rendered_widgets):
        """Place the assumed two widgets side by side"""
        output = """<div class="row collapse">
        <div class="medium-6 column">{0:s}</div>
        <div class="medium-6 column">{1:s}</div>
        </div>""".format(*rendered_widgets)
        return output


class MultitypeQueryField(forms.MultiValueField):
    """
    Field that accepts a text query and a query type
    input, and validates the query according to the type.
    """

    def __init__(self, choices, validators, *args, **kwargs):
        """
        :param validators:  A dict that maps query type
        values to validators.
        """
        if validators is None:
            validators = {}
        # Prevent Django from affecting "required" by setting the fields
        # ourselves
        super(MultitypeQueryField, self).__init__(fields=(), *args, **kwargs)
        self.fields = (
            forms.ChoiceField(choices=choices),
            forms.CharField(min_length=1),
        )
        self.widget = MultitypeQueryWidget(
            (forms.Select(choices=choices), forms.TextInput())
        )
        self.query_validators = validators

    def validate(self, value):
        query = value[1]
        query_type = value[0]
        if query_type in self.query_validators:
            self.query_validators[query_type](query)

    def compress(self, data_list):
        return data_list


class ErrorLogSearchForm(forms.Form):
    """Form for searching in radius error log"""

    QUERY_TYPES = (
        ('username', 'Username'),
        ('client', 'Client'),
        ('port', 'Port'),
        ('message', 'Message'),
    )
    TIME_TYPES = (
        ('hours', 'Hour(s)'),
        ('timestamp', 'Timespan'),
        ('', 'All time'),
    )
    LOG_ENTRY_TYPES = (
        ('', 'All'),
        ('auth', 'Auth'),
        ('error', 'Error'),
        ('info', 'Info'),
        ('proxy', 'Proxy'),
    )
    query = MultitypeQueryField(
        QUERY_TYPES, validators={'port': validate_integer}, label='Search for'
    )
    log_entry_type = forms.ChoiceField(required=False, choices=LOG_ENTRY_TYPES)
    time = MultitypeQueryField(
        TIME_TYPES,
        validators={
            'hours': validate_integer,
            'timestamp': validate_datetime_with_slack,
        },
        required=False,
        label='Time options',
    )

    def __init__(self, *args, **kwargs):
        super(ErrorLogSearchForm, self).__init__(*args, **kwargs)
        css_class = 'medium-4'
        self.attrs = set_flat_form_attributes(
            form_method='get',
            form_class='custom',
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self['query']], css_classes=css_class),
                        FormColumn(
                            fields=[self['log_entry_type']], css_classes=css_class
                        ),
                        FormColumn(fields=[self['time']], css_classes=css_class),
                    ]
                ),
                SubmitField(name='send', value='Search', css_classes='small'),
            ],
        )

    def clean_time(self):
        if self.cleaned_data["time"]:
            time_type, time = self.cleaned_data["time"]
            if time_type == "hours":
                validate_timedelta_for_overflow(hours=int(time))
            return time


class AccountLogSearchForm(forms.Form):
    """Form for searching in the radius account log"""

    QUERY_TYPES = (
        ('username', 'Username'),
        ('framedipaddress', 'User Hostname/IP Address'),
        ('nasipaddress', 'IP Address'),
        ('iprange', 'IP-range'),
    )
    TIME_TYPES = (
        ('days', 'Day(s)'),
        ('timestamp', 'Timespan'),
        ('', 'All time'),
    )
    PORT_TYPES = (
        ('', 'All'),
        ('dot1x', '.1x'),
        ('isdn', 'ISDN'),
        ('modem', 'Modem'),
        ('vpn', 'VPN'),
    )
    DNS_LOOKUPS = (
        ('userdns', 'User IP'),
        ('nasdns', 'NAS IP'),
    )
    query = MultitypeQueryField(
        QUERY_TYPES,
        validators={'nasipaddress': validate_ipv4_address, 'iprange': validate_cidr},
        label='Search for',
    )
    time = MultitypeQueryField(
        TIME_TYPES,
        validators={
            'days': validate_integer,
            'timestamp': validate_datetime_with_slack,
        },
        required=False,
        label='Time options',
    )
    port_type = forms.ChoiceField(required=False, choices=PORT_TYPES)
    dns_lookup = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple, required=False, choices=DNS_LOOKUPS
    )

    def __init__(self, *args, **kwargs):
        super(AccountLogSearchForm, self).__init__(*args, **kwargs)
        css_class_large = 'large-4 medium-6'
        css_class_small = 'large-2 medium-6'
        self.attrs = set_flat_form_attributes(
            form_method='get',
            form_class='custom',
            form_fields=[
                FormRow(
                    fields=[
                        FormColumn(fields=[self['query']], css_classes=css_class_large),
                        FormColumn(fields=[self['time']], css_classes=css_class_large),
                        FormColumn(
                            fields=[self['port_type']], css_classes=css_class_small
                        ),
                        FormColumn(
                            fields=[self['dns_lookup']], css_classes=css_class_small
                        ),
                    ]
                ),
                SubmitField(name='send', value='Search', css_classes='small'),
            ],
        )

    def clean_time(self):
        if self.cleaned_data["time"]:
            time_type, time = self.cleaned_data["time"]
            if time_type == "days":
                validate_timedelta_for_overflow(days=int(time))
            return time


class AccountChartsForm(forms.Form):
    """Form for displaying top talkers"""

    CHARTS = (
        ('sentrecv', 'Bandwidth hogs'),
        ('recv', 'Downloaders'),
        ('sent', 'Uploaders'),
    )

    days = forms.FloatField(min_value=0.5, initial=7, label='Day(s)')
    charts = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple, choices=CHARTS, initial=CHARTS[0]
    )

    def __init__(self, *args, **kwargs):
        super(AccountChartsForm, self).__init__(*args, **kwargs)
        self.attrs = set_flat_form_attributes(
            form_method='get',
            form_fields=[self['days'], self['charts']],
            submit_field=SubmitField('send', 'Show me', css_classes='small'),
        )

    def clean_days(self):
        days = self.cleaned_data["days"]
        validate_timedelta_for_overflow(days=days)

        return days
