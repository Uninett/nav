#
# Copyright (C) 2015 Uninett AS
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
"""Widget for displaying a sensor"""

from nav.models.manage import Sensor
from . import Navlet, NAVLET_MODE_EDIT
from .forms import SensorForm


class SensorWidget(Navlet):
    """Widget for displaying a sensor."""

    title = 'Sensor'
    description = 'Displays a sensor'
    is_editable = True
    is_title_editable = True
    can_be_added = False  # Can only be added from the sensors on the
    # "Environment sensors" tab in room info

    def get_template_basename(self):
        return 'sensor'

    def get_context_data(self, *args, **kwargs):
        context = super(SensorWidget, self).get_context_data(*args, **kwargs)
        try:
            sensor = Sensor.objects.get(pk=self.preferences.get('sensor_id'))
        except Sensor.DoesNotExist:
            sensor = None

        context['sensor'] = sensor

        if self.mode == NAVLET_MODE_EDIT:
            if 'show_graph' in self.preferences:
                context['form'] = SensorForm(self.preferences)
            else:
                context['form'] = SensorForm()

        self.title = self.preferences.get('title', SensorWidget.title)
        return context

    def post(self, request, **kwargs):
        """Save preferences"""
        form = SensorForm(request.POST)
        return super(SensorWidget, self).post(request, form=form)
