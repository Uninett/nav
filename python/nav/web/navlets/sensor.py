#
# Copyright (C) 2015 UNINETT AS
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
"""Widget for displaying a sensor"""

from nav.models.manage import Sensor
from . import Navlet


class SensorWidget(Navlet):
    """Widget for displaying a sensor."""

    title = 'Sensor'
    description = 'Displays a sensor'
    is_title_editable = True
    can_be_added = False  # Can only be added from the sensors on the
                          # "Environment sensors" tab in room info

    def get_template_basename(self):
        return 'sensor'

    def get_context_data(self, *args, **kwargs):
        context = super(SensorWidget, self).get_context_data(*args, **kwargs)
        sensor_id = self.preferences.get('sensor_id')
        self.title = self.preferences.get('title', SensorWidget.title)
        context['sensor'] = Sensor.objects.get(pk=sensor_id)

        return context
