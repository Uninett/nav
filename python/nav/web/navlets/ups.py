#
# Copyright (C) 2016 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Module containing UPSWidget"""

from django.http import HttpResponse
from django.db.models import Q

from nav.models.profiles import AccountNavlet
from nav.models.manage import Netbox
from . import Navlet, NAVLET_MODE_EDIT
from .forms import UpsWidgetForm


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

    def get_context_data(self, *args, **kwargs):
        context = super(UpsWidget, self).get_context_data(*args, **kwargs)
        navlet = AccountNavlet.objects.get(pk=self.navlet_id)
        self.title = navlet.preferences.get('title', 'UPS status')

        netboxid = navlet.preferences.get('netboxid')
        if self.mode == NAVLET_MODE_EDIT:
            if netboxid:
                form = UpsWidgetForm(self.preferences)
            else:
                form = UpsWidgetForm()
            context['form'] = form
        else:
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

    def post(self, request):
        """Save preferences"""
        navlet = AccountNavlet.objects.get(pk=self.navlet_id,
                                           account=request.account)
        form = UpsWidgetForm(request.POST)
        if form.is_valid():
            netboxid = form.cleaned_data['netboxid'].pk
            navlet.preferences['netboxid'] = netboxid
            navlet.save()
            return HttpResponse()
        else:
            return HttpResponse(form.errors, status=400)
