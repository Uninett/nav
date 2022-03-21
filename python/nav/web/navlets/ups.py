#
# Copyright (C) 2016 Uninett AS
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
"""Module containing UPSWidget"""

from django import forms
from django.db.models import Q
from urllib.parse import urlparse

from nav.models.manage import Netbox, Sensor
from . import Navlet


class UpsWidgetForm(forms.Form):
    """Form for choosing an UPS"""

    netboxid = forms.ModelChoiceField(
        queryset=Netbox.ups_objects.all(), label='Choose UPS'
    )
    external_link = forms.CharField(
        required=False, label='External link (must start with http)'
    )

    def clean_netboxid(self):
        """Cheat and return the netboxid instead of the object

        This is done because the result is serialized
        """
        netbox = self.cleaned_data.get('netboxid')
        return netbox.pk

    def clean_external_link(self):
        link = self.cleaned_data.get('external_link')
        if link and not urlparse(link).scheme.startswith('http'):
            raise forms.ValidationError('Link needs to start with http or https')
        return link


class UpsWidget(Navlet):
    """Widget for displaying a binary on/off widget"""

    title = 'UPS status'
    is_editable = True
    is_title_editable = True
    ajax_reload = True
    description = 'Display UPS status'
    refresh_interval = 30000  # 30 seconds

    def get_template_basename(self):
        return 'ups'

    def get_context_data_edit(self, context):
        netboxid = self.preferences.get('netboxid')
        if netboxid:
            form = UpsWidgetForm(self.preferences)
        else:
            form = UpsWidgetForm()
        context['form'] = form
        return context

    def get_context_data_view(self, context):
        netboxid = self.preferences.get('netboxid')
        if not netboxid:
            return context

        try:
            netbox = Netbox.objects.get(pk=netboxid)
        except Netbox.DoesNotExist:
            context["doesnotexist"] = netboxid
            return context

        context['netbox'] = netbox

        # internal names selected from ups-mib and powernet-mib.

        # Input
        context['input_voltages'] = netbox.sensor_set.filter(
            Q(internal_name__contains="InputVoltage")
            | Q(internal_name__contains="InputLineVoltage")
        ).filter(precision__isnull=True)

        # Output
        output_voltages = netbox.sensor_set.filter(
            Q(internal_name__contains="OutputVoltage")
            | Q(internal_name__contains="OutputLineVoltage")
        ).filter(precision__isnull=True)
        output_power = netbox.sensor_set.filter(internal_name__contains="OutputPower")

        if len(output_voltages) != len(output_power):
            output_power = [None] * len(output_voltages)
        context['output'] = zip(output_voltages, output_power)

        # Battery
        context['battery_times'] = (
            BatteryTimesProxy(sensor)
            for sensor in netbox.sensor_set.filter(
                internal_name__in=[
                    'upsEstimatedMinutesRemaining',
                    'upsAdvBatteryRunTimeRemaining',
                ]
            )
        )

        context['battery_capacity'] = netbox.sensor_set.filter(
            internal_name__in=[
                'upsHighPrecBatteryCapacity',
                'upsEstimatedChargeRemaining',
            ]
        )

        context['temperatures'] = netbox.sensor_set.filter(
            internal_name__in=['upsHighPrecBatteryTemperature', 'upsBatteryTemperature']
        )

        return context

    def post(self, request, **kwargs):
        """Save preferences"""
        return super(UpsWidget, self).post(request, form=UpsWidgetForm(request.POST))


class BatteryTimesProxy:
    """Proxies access to Sensor objects that represent remaining battery time.

    For consistency, we want the widget to always display remaining time in minutes,
    but we need to scale the value for sensors that report the remaining time in
    seconds.
    """

    def __init__(self, proxied_sensor: Sensor):
        self.__proxied = proxied_sensor

    def __getattr__(self, name):
        return getattr(self.__proxied, name)

    @property
    def unit_of_measurement(self):
        """Reports unit as minutes for sensors that measure seconds"""
        if self.__proxied.unit_of_measurement == Sensor.UNIT_SECONDS:
            return Sensor.UNIT_MINUTES
        else:
            return self.__proxied.unit_of_measurement

    def get_metric_name(self):
        """Surrounds the metric name in Graphite scale expressions if conversion from
        seconds to minutes is needed for the proxied sensor.
        """
        name = self.__proxied.get_metric_name()
        if self.__proxied.unit_of_measurement == Sensor.UNIT_SECONDS:
            return f"round(scale({name},0.0166),0)"
        else:
            return name
