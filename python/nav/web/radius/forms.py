from django import forms
#from nav.django.forms import CIDRField, MultiSelectFormField


class LogSearchForm(forms.Form):
    """Base class"""

    query = forms.CharField(min_length=1)
    query_type = forms.ChoiceField(choices=[])


class ErrorLogSearchForm(forms.Form):
    QUERY_TYPES = (
        ('username', 'Username'),
        ('client', 'Client'),
        ('port', 'Port'),
        ('message', 'Message'),
    )
    LOG_ENTRY_TYPES = (
        ('all', 'All'),
        ('auth', 'Auth'),
        ('error', 'Error'),
        ('info', 'Info'),
        ('proxy', 'Proxy'),
    )

    log_entry_type = forms.ChoiceField(choices=LOG_ENTRY_TYPES)

    def __init__(self, *args, **kwargs):
        super(ErrorLogSearchForm, self).__init__(*args, **kwargs)
        self.fields['querytype'].choices = self.QUERY_TYPES


class AccountLogSearchForm(forms.Form):
    QUERY_TYPES = (
        ('username', 'Username'),
        ('framedipaddress', 'User Hostname/IP Address'),
        ('nasipaddress', 'IP Address'),
        ('iprange', 'IP-range'),
    )
    PORT_TYPES = (
        ('all', 'All'),
        ('dot1x', '.1x'),
        ('isdn', 'ISDN'),
        ('modem', 'Modem'),
        ('vpn', 'VPN'),
    )
    DNS_LOOKUPS = (
        ('userdns', 'User IP'),
        ('nasdns', 'NAS IP'),
    )

    port_types = forms.ChoiceField(choices=PORT_TYPES)
    dns_lookup = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        super(AccountLogSearchForm, self).__init__(*args, **kwargs)
        self.fields['query_type'].choices = self.QUERY_TYPES


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