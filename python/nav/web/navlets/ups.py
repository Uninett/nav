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
from django.utils.six.moves.urllib.parse import urlparse

from nav.models.manage import Netbox
from . import Navlet


class UpsWidgetForm(forms.Form):
    """Form for choosing an UPS"""
    netboxid = forms.ModelChoiceField(queryset=Netbox.ups_objects.all(),
                                      label='Choose UPS')
    external_link = forms.CharField(
        required=False, label='External link (must start with http)')

    def clean_netboxid(self):
        """Cheat and return the netboxid instead of the object

        This is done because the result is serialized
        """
        netbox = self.cleaned_data.get('netboxid')
        return netbox.pk

    def clean_external_link(self):
        link = self.cleaned_data.get('external_link')
        if link and not urlparse(link).scheme.startswith('http'):
            raise forms.ValidationError(
                'Link needs to start with http or https')
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

        netbox = Netbox.objects.get(pk=netboxid)
        context['netbox'] = netbox

        # internal names selected from ups-mib and powernet-mib.

        # Input
        context['input_voltages'] = netbox.sensor_set.filter(
            Q(internal_name__contains="InputVoltage") |
            Q(internal_name__contains="InputLineVoltage")
        ).filter(precision__isnull=True)

        # Output
        output_voltages = netbox.sensor_set.filter(
            Q(internal_name__contains="OutputVoltage") |
            Q(internal_name__contains="OutputLineVoltage")
        ).filter(precision__isnull=True)
        output_power = netbox.sensor_set.filter(
            internal_name__contains="OutputPower")

        if len(output_voltages) != len(output_power):
            output_power = [None] * len(output_voltages)
        context['output'] = zip(output_voltages, output_power)

        # Battery
        context['battery_times'] = netbox.sensor_set.filter(
            internal_name__in=['upsEstimatedMinutesRemaining',
                               'upsAdvBatteryRunTimeRemaining'])

        context['battery_capacity'] = netbox.sensor_set.filter(
            internal_name__in=['upsHighPrecBatteryCapacity',
                               'upsEstimatedChargeRemaining'])

        context['temperatures'] = netbox.sensor_set.filter(
            internal_name__in=['upsHighPrecBatteryTemperature',
                               'upsBatteryTemperature'])

        return context

    def post(self, request, **kwargs):
        """Save preferences"""
        return super(UpsWidget, self).post(
            request, form=UpsWidgetForm(request.POST))
