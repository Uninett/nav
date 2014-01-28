from datetime import datetime

from django import forms
from django.core.validators import validate_ipv4_address
from django.core.validators import validate_integer as django_validate_integer

from crispy_forms.helper import FormHelper
from crispy_forms_foundation.layout import (Layout, Row, Column, Field,
                                            MultiWidgetField, Submit)
from django.utils.safestring import mark_safe

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

    def format_output(self, rendered_widgets):
        """Place the assumed two widgets side by side"""
        output = u"""<div class="row collapse">
        <div class="medium-6 column">{0:s}</div>
        <div class="medium-6 column">{1:s}</div>
        </div>""".format(*rendered_widgets)
        return output


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
            forms.ChoiceField(choices=choices),
            forms.CharField(min_length=1)
        )
        self.widget = MultitypeQueryWidget(
            (forms.Select(choices=choices),
             forms.TextInput())
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

    def __init__(self, *args, **kwargs):
        super(ErrorLogSearchForm, self).__init__(*args, **kwargs)
        css_class = 'medium-4'
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'GET'
        self.helper.form_class = 'custom'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class=css_class),
                Column('log_entry_type', css_class=css_class),
                Column('time', css_class=css_class)
            ),
            Submit('send', 'Search', css_class='small')
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

    def __init__(self, *args, **kwargs):
        super(AccountLogSearchForm, self).__init__(*args, **kwargs)
        css_class = 'medium-6'
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'GET'
        self.helper.form_class = 'custom'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class=css_class),
                Column('time', css_class=css_class)
            ),
            Row(
                Column('port_type', css_class=css_class),
                Column('dns_lookup', css_class=css_class),
            ),
            Submit('send', 'Search', css_class='small')
        )


class MyCheckBoxSelectMultiple(forms.CheckboxSelectMultiple):
    """Display the list of checkboxes with inline style"""
    def render(self, name, value, attrs=None, choices=()):
        html = super(MyCheckBoxSelectMultiple, self).render(
            name, value, attrs, choices)
        return mark_safe(html.replace('<ul>', '<ul class="inline-list">'))


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
        widget=MyCheckBoxSelectMultiple(),
        initial=CHARTS[0])

    def __init__(self, *args, **kwargs):
        super(AccountChartsForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_action = ''
        self.helper.form_method = 'GET'
        self.helper.layout = Layout(
            Row(
                Column('days', css_class='medium-3'),
                Column('charts', css_class='medium-9')
            ),
            Submit('send', 'Create', css_class='small')
        )
