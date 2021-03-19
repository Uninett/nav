#
# Copyright (C) 2012 Uninett AS
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
"""maintenance handler plugin"""

from nav.eventengine.plugin import EventHandler
from nav.eventengine.alerts import AlertGenerator


class MaintenanceStateHandler(EventHandler):
    """Accepts maintenanceState events"""

    handled_types = ('maintenanceState',)

    def handle(self):
        event = self.event

        if event.state == event.STATE_STATELESS:
            self._logger.info('Ignoring stateless maintenanceState event')
        else:
            self._post_alert(event)

        event.delete()

    def _post_alert(self, event):
        alert = AlertGenerator(event)
        alert.alert_type = (
            'onMaintenance' if event.state == event.STATE_START else 'offMaintenance'
        )
        alert.history_vars = dict(alert)
        if alert.is_event_duplicate():
            self._logger.info('Ignoring duplicate event')
        else:
            alert.post()
