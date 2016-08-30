"""Module containing some of the forms used in widgets"""

from django import forms

from nav.models.manage import Netbox


class AlertWidgetForm(forms.Form):
    """Form for the alert widget"""
    on_message = forms.CharField(
        label='Message when alert is active',
        initial='The alert is active')
    off_message = forms.CharField(
        label='Message when alert is inactive (ok)',
        initial='No alert')
    metric = forms.CharField(
        label='Metric path to fetch value from',
        widget=forms.TextInput(attrs={'placeholder':'nav.metric.path.value'}))
    on_state = forms.ChoiceField(
        label='When is the alert considered "on"',
        choices=(('1', 'When the value is 1'),
                 ('0', 'When the value is 0 (zero)')))
    alert_type = forms.ChoiceField(
        label='What to display in "on" state',
        choices=(('alert', 'A red alert'), ('warning', 'An orange warning')))


class UpsWidgetForm(forms.Form):
    """Form for choosing an UPS"""
    netboxid = forms.ModelChoiceField(queryset=Netbox.ups_objects.all())
