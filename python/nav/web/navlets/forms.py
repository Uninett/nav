"""Module containing some of the forms used in widgets"""

from django import forms

from nav.models.manage import Sensor, Room

from nav.web.crispyforms import set_flat_form_attributes, FlatFieldset


class AlertWidgetForm(forms.Form):
    """Form for the alert widget"""

    on_message = forms.CharField(
        label='Message when alert is active', initial='The alert is active'
    )
    off_message = forms.CharField(
        label='Message when alert is inactive (ok)', initial='No alert'
    )
    sensor = forms.ChoiceField(choices=(), required=False)
    metric = forms.CharField(
        label='Metric path to fetch value from',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'nav.metric.path.value'}),
    )
    on_state = forms.ChoiceField(
        label='When is the alert considered "on"',
        choices=(('1', 'When the value is 1'), ('0', 'When the value is 0 (zero)')),
    )
    alert_type = forms.ChoiceField(
        label='What to display in "on" state',
        choices=(('alert', 'A red alert'), ('warning', 'An orange warning')),
    )

    def __init__(self, *args, **kwargs):
        """Init"""
        super(AlertWidgetForm, self).__init__(*args, **kwargs)
        self.fields['sensor'].choices = [('', '----------')] + [
            (s.pk, str(s))
            for s in Sensor.objects.filter(unit_of_measurement='boolean').order_by(
                'human_readable'
            )
        ]

        self.attrs = set_flat_form_attributes(
            form_fields=[
                self['on_message'],
                self['off_message'],
                FlatFieldset(
                    legend='Choose sensor or fill in metric',
                    fields=[self['sensor'], self['metric']],
                ),
                self['on_state'],
                self['alert_type'],
            ]
        )

    def clean(self):
        """Make sure either metric name or sensor is specified"""
        cleaned_data = super(AlertWidgetForm, self).clean()
        if not (cleaned_data.get('metric') or cleaned_data.get('sensor')):
            raise forms.ValidationError(
                'Need either metric name or a sensor', code='metric-or-sensor-required'
            )
        return cleaned_data


class SensorForm(forms.Form):
    """Form for choosing to show graph or not for a sensor widget"""

    show_graph = forms.BooleanField(initial=True, required=False)


class PduWidgetForm(forms.Form):
    """Form for choosing a room"""

    room_id = forms.ChoiceField(choices=(), label='Room')
    limits = forms.IntegerField(label='Max allowed load in amperes, per bank/circuit')

    def __init__(self, *args, **kwargs):
        super(PduWidgetForm, self).__init__(*args, **kwargs)

        self.fields['room_id'].choices = [('', '----------')] + [
            (r.pk, str(r))
            for r in Room.objects.filter(
                netboxes__category='POWER',
                netboxes__sensors__internal_name__startswith='rPDULoadStatusLoad',
            ).distinct('id')
        ]
