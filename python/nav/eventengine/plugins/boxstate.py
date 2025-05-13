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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
""" "boxState event plugin"""

from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins import delayedstate
from nav.models.manage import Netbox


class BoxStateHandler(delayedstate.DelayedStateHandler):
    """Accepts boxState events"""

    handled_types = ('boxState',)
    WARNING_WAIT_TIME = 'boxDown.warning'
    ALERT_WAIT_TIME = 'boxDown.alert'

    def _is_internally_down(self):
        netbox = self.get_target()
        return netbox.up != netbox.UP_UP

    def _set_internal_state_down(self):
        shadow = self._verify_shadow()
        state = Netbox.UP_SHADOW if shadow else Netbox.UP_DOWN
        self._set_internal_state(state)

    def _set_internal_state_up(self):
        self._set_internal_state(Netbox.UP_UP)

    def _set_internal_state(self, state):
        netbox = self.get_target()
        netbox.up = state
        Netbox.objects.filter(id=netbox.id).update(up=state)

    def get_target(self):
        return self.event.netbox

    def _get_up_alert(self):
        alert = AlertGenerator(self.event)
        is_shadow = self.event.netbox.up == self.event.netbox.UP_SHADOW
        alert.alert_type = "boxSunny" if is_shadow else "boxUp"
        return alert

    def _post_down_warning(self):
        """Posts the actual warning alert"""
        alert = AlertGenerator(self.event)
        alert.state = self.event.STATE_STATELESS

        shadow = self._verify_shadow()
        if shadow:
            alert.alert_type = 'boxShadowWarning'
            self._set_internal_state(Netbox.UP_SHADOW)
        else:
            alert.alert_type = 'boxDownWarning'

        self._logger.info("%s: Posting %s alert", self.event.netbox, alert.alert_type)
        alert.post()

    def _get_down_alert(self):
        alert = AlertGenerator(self.event)
        if self._verify_shadow():
            alert.alert_type = 'boxShadow'
            self._set_internal_state(Netbox.UP_SHADOW)
        else:
            alert.alert_type = 'boxDown'
        return alert
