from django import forms
from django.core.validators import validate_ipv4_address

from nav.util import is_valid_cidr


def validate_cidr(value):
    if not value or not is_valid_cidr(value):
        raise forms.ValidationError(
            "Value must be a valid CIDR address")


class TimestampSlackWidget(forms.MultiWidget):
    """
    Widget for TimestampSlackField. It combines a
    DateTimeInput with a TextInput.
    """

    def decompress(self, value):
        return [value]


class TimestampSlackField(forms.MultiValueField):
    """
    Field that combines a Datetime value with a
    'slack' value given in minutes.
    """
    required = False
    fields = (
        forms.DateTimeField(),
        forms.IntegerField(min_value=1, max_value=999)
    )
    widget = TimestampSlackWidget(
        # When using MultivalueField initial does not work on
        # the fields and must be passed to the widgets
        (forms.DateTimeInput(attrs={'value': 'YYYY-MM-DD hh:mm'}),
         forms.TextInput(attrs={'value': '1'}))
    )

    def compress(self, data_list):
        return data_list


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

    def __init__(self, choices, validators, *args, **kwargs):
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


class LogSearchForm(forms.Form):
    """Base class"""
    days = forms.FloatField(
        min_value=0.5,
        initial=0.5,
        label='Last # day(s)',
        required=False)
    timestamp = TimestampSlackField(required=False)
    timemode = forms.ChoiceField(
        required=False,
        choices=(('days', ''),
                 ('timestamp', ''),
                 ('', '')))


class ErrorLogSearchForm(LogSearchForm):
    QUERY_TYPES = (
        ('username', 'Username'),
        ('client', 'Client'),
        ('port', 'Port'),
        ('message', 'Message'),
    )
    LOG_ENTRY_TYPES = (
        ('', 'All'),
        ('auth', 'Auth'),
        ('error', 'Error'),
        ('info', 'Info'),
        ('proxy', 'Proxy'),
    )
    query = MultitypeQueryField(
        choices=QUERY_TYPES,
        validators=({
            # TODO
        })
    )
    log_entry_type = forms.ChoiceField(choices=LOG_ENTRY_TYPES)


class AccountLogSearchForm(LogSearchForm):
    QUERY_TYPES = (
        ('username', 'Username'),
        ('framedipaddress', 'User Hostname/IP Address'),
        ('nasipaddress', 'IP Address'),
        ('iprange', 'IP-range'),
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
    port_type = forms.ChoiceField(required=False, choices=PORT_TYPES)
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