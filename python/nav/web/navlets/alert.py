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
"""Module containing SensorWidget"""

from nav.metrics.graphs import get_simple_graph_url
from nav.models.manage import Sensor
from . import Navlet, NAVLET_MODE_EDIT
from .forms import AlertWidgetForm


class AlertWidget(Navlet):
    """Widget for displaying a binary on/off widget"""

    title = 'Alert'
    is_editable = True
    is_title_editable = True
    ajax_reload = True
    description = 'Displays the state of a metric, for instance if ' \
                  'a security system is on or off.'
    refresh_interval = 30000  # 30 seconds

    def get_template_basename(self):
        return 'alert'

    def get_context_data(self, *args, **kwargs):
        context = super(AlertWidget, self).get_context_data(**kwargs)
        self.title = self.preferences.get('title', 'Alert')
        metric = self.preferences.get('metric')

        try:
            sensorid = int(self.preferences.get('sensor', 0))
        except ValueError:
            sensorid = None

        if not metric and sensorid:
            metric = Sensor.objects.get(pk=sensorid).get_metric_name()
            self.preferences['metric'] = metric

        if self.mode == NAVLET_MODE_EDIT:
            if metric:
                form = AlertWidgetForm(self.preferences)
            else:
                form = AlertWidgetForm()
            context['form'] = form
        else:
            if not metric:
                return context
            context['data_url'] = get_simple_graph_url(
                metric, time_frame='10minutes', format='json')
            context.update(self.preferences)
        return context

    def post(self, request, **kwargs):
        """Save preferences"""
        form = AlertWidgetForm(request.POST)
        return super(AlertWidget, self).post(request, form=form)
