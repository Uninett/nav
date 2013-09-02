from datetime import datetime

from django import forms
from django.core.validators import validate_ipv4_address
from django.core.validators import validate_integer as django_validate_integer

from nav.util import is_valid_cidr


def validate_integer(value):
    try:
        django_validate_integer(value)
    except forms.ValidationError:
        raise forms.ValidationError('Must be a number!')


def validate_cidr(value):
    if not value or not is_valid_cidr(value):
        raise forms.ValidationError(
            'Must be a valid CIDR address!')


def validate_datetime_with_slack(value):
    try:
        time, slack = value.split('|')
        datetime.strptime(time, '%Y-%m-%d %H:%M')
        int(slack)
    except (ValueError, TypeError):
        raise forms.ValidationError(
            'Must be of this format YYYY-MM-DD hh:mm|slack')


class MultitypeQueryWidget(forms.MultiWidget):
    """
    Widget for MultitypeQueryField
    """
    def decompress(self, value):
        return [value]


class MultitypeQueryField(forms.MultiValueField):
    """
    Field that accepts a text query and a query type
    input, and validates the query according to the type.
    """

    def __init__(self, choices, validators={}, *args, **kwargs):
        """
        :param validators:  A dict that maps query type
        values to validators.
        """
        super(MultitypeQueryField, self).__init__(*args, **kwargs)
        self.fields = (
            forms.CharField(min_length=1),
            forms.ChoiceField(choices=choices)
        )
        self.widget = MultitypeQueryWidget(
            (forms.TextInput(),
             forms.Select(choices=choices))
        )
        self.query_validators = validators

    def validate(self, value):
        query = value[0]
        query_type = value[1]
        if query_type in self.query_validators:
            self.query_validators[query_type](query)

    def compress(self, data_list):
        return data_list


class ErrorLogSearchForm(forms.Form):
    QUERY_TYPES = (
        ('username', 'Username'),
        ('client', 'Client'),
        ('port', 'Port'),
        ('message', 'Message'),
    )
    TIME_TYPES = (
        ('hours', 'Last # hour(s)'),
        ('timestamp', 'Timestamp'),
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
        QUERY_TYPES,
        validators={
            'port': validate_integer
        })
    log_entry_type = forms.ChoiceField(
        required=False,
        choices=LOG_ENTRY_TYPES)
    time = MultitypeQueryField(
        TIME_TYPES,
        validators={
            'hours': validate_integer,
            'timestamp': validate_datetime_with_slack
        },
        required=False
    )


class AccountLogSearchForm(forms.Form):
    QUERY_TYPES = (
        ('username', 'Username'),
        ('framedipaddress', 'User Hostname/IP Address'),
        ('nasipaddress', 'IP Address'),
        ('iprange', 'IP-range'),
    )
    TIME_TYPES = (
        ('days', 'Last # day(s)'),
        ('timestamp', 'Timestamp'),
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
        validators={
            'nasipaddress': validate_ipv4_address,
            'iprange': validate_cidr
        }
    )
    time = MultitypeQueryField(
        TIME_TYPES,
        validators={
            'days': validate_integer,
            'timestamp': validate_datetime_with_slack
        },
        required=False
    )
    port_type = forms.ChoiceField(
        required=False,
        choices=PORT_TYPES)
    dns_lookup = forms.MultipleChoiceField(
        required=False,
        choices=DNS_LOOKUPS,
        widget=forms.CheckboxSelectMultiple)


class AccountChartsForm(forms.Form):
    CHARTS = (
        ('sentrecv', 'Overall'),
        ('recv', 'Download'),
        ('sent', 'Upload'),
    )

    days = forms.FloatField(
        min_value=0.5,
        initial=7,
        label='Last # day(s)')
    charts = forms.MultipleChoiceField(
        choices=CHARTS,
        widget=forms.CheckboxSelectMultiple)