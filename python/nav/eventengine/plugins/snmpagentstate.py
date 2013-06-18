#
# Copyright (C) 2012 UNINETT AS
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
"""Uses delayedstatehandler to implement a handler for snmpagentstate"""

from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins.delayedstate import DelayedStateHandler


class SnmpAgentStateHandler(DelayedStateHandler):
    """Accepts snmpAgentState events"""

    HAS_WARNING_ALERT = False
    ALERT_WAIT_TIME = 'snmpAgentDown.alert'
    handled_types = ('snmpAgentState', )

    __waiting_for_resolve = {}

    def get_target(self):
        return self.event.netbox

    def _get_up_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = 'snmpAgentUp'
        return alert

    def _get_down_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = 'snmpAgentDown'
        return alert

    def _post_down_warning(self):
        pass
