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
"""Uses delayedstatehandler to implement a handler for snmpagentstate"""

from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins.delayedstate import DelayedStateHandler
from nav.models.manage import Netbox


class SnmpAgentStateHandler(DelayedStateHandler):
    """Accepts snmpAgentState events"""

    HAS_WARNING_ALERT = False
    ALERT_WAIT_TIME = 'snmpAgentDown.alert'
    handled_types = ('snmpAgentState',)

    def get_target(self):
        return self.event.netbox

    def _get_up_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = 'snmpAgentUp'
        return alert

    def _get_down_alert(self):
        if self._is_netbox_currently_up():
            alert = AlertGenerator(self.event)
            alert.alert_type = 'snmpAgentDown'
            return alert
        else:
            self._logger.info(
                "%s has gone down in the meantime, not posting snmpAgentDown alert",
                self.get_target(),
            )

    def _is_netbox_currently_up(self):
        row = Netbox.objects.filter(id=self.get_target().id).values_list('up')[0]
        return row[0] == Netbox.UP_UP

    def _post_down_warning(self):
        pass
