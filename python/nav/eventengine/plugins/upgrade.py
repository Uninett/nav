#
# Copyright (C) 2023 Sikt
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
"""software/firmware/hardware upgrade handler plugin"""

from nav.eventengine.plugin import EventHandler
from nav.eventengine.alerts import AlertGenerator


class UpgradeHandler(EventHandler):
    """Accepts deviceNotice events"""

    handled_types = ('deviceNotice',)

    def handle(self):
        event = self.event

        if event.state != event.STATE_STATELESS:
            self._logger.info('Ignoring stateful deviceNotice event')
        else:
            self._post_alert(event)

        event.delete()

    def _post_alert(self, event):
        alert = AlertGenerator(event)
        if alert.alert_type in (
            "deviceHwUpgrade",
            "deviceSwUpgrade",
            "deviceFwUpgrade",
        ):
            alert.history_vars["old_version"] = alert.get("old_version", "N/A")
            alert.history_vars["new_version"] = alert.get("new_version", "N/A")

        alert.post()
