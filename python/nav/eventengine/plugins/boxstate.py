#
# Copyright (C) 2012 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
""""boxState event plugin"""
from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins import delayedstate

class BoxStateHandler(delayedstate.DelayedStateHandler):
    """Accepts boxState events"""
    handled_types = ('boxState',)
    WARNING_WAIT_TIME = 'boxDown.warning'
    ALERT_WAIT_TIME = 'boxDown.alert'
    __waiting_for_resolve = {}

    def _register_internal_down_state(self):
        netbox = self.get_target()
        netbox.up = netbox.UP_DOWN
        netbox.save()

    def get_target(self):
        return self.event.netbox

    def _get_up_alert(self):
        alert = AlertGenerator(self.event)
        is_shadow = self.event.netbox.up == self.event.netbox.UP_SHADOW
        alert.alert_type = "boxSunny" if is_shadow else "boxUp"

        netbox = self.get_target()
        netbox.up = netbox.UP_UP
        netbox.save()
        return alert

    def _post_down_warning(self):
        """Posts the actual warning alert"""
        alert = AlertGenerator(self.event)
        self._logger.info("%s: Posting boxDownWarning alert",
                          self.event.netbox)
        alert.alert_type = "boxDownWarning"
        alert.state = self.event.STATE_STATELESS
        alert.post()

    def _get_down_alert(self):
        alert = AlertGenerator(self.event)
        shadow = self._verify_shadow()
        alert.alert_type = 'boxShadow' if shadow else 'boxDown'
        return alert
