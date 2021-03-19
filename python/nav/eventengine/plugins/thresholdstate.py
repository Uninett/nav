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
"""thresholdstate handler plugin"""

from nav.eventengine.plugin import EventHandler
from nav.eventengine.alerts import AlertGenerator


class ThresholdStateHandler(EventHandler):
    """Accepts thresholdState events"""

    handled_types = ('thresholdState',)

    def handle(self):
        event = self.event

        if event.state == event.STATE_STATELESS:
            self._logger.info('Ignoring stateless thresholdState event')
        else:
            self._post_alert(event)

        event.delete()

    def _post_alert(self, event):
        alert = AlertGenerator(event)
        alert.alert_type = (
            'exceededThreshold'
            if event.state == event.STATE_START
            else 'belowThreshold'
        )

        if alert.is_event_duplicate():
            self._logger.info('Ignoring duplicate alert')
        else:
            alert.post()
