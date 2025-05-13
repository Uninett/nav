#
# Copyright (C) 2017 Uninett AS
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
""" "bgpState event plugin"""

from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugins import delayedstate


class BGPStateHandler(delayedstate.DelayedStateHandler):
    """Accepts bgpState events"""

    handled_types = ('bgpState',)
    HAS_WARNING_ALERT = False
    ALERT_WAIT_TIME = 'bgpDown.alert'

    def get_target(self):
        """Returns the peering session this event is about.

        :rtype: nav.models.manage.GatewayPeerSession
        """
        return self.event.get_subject()

    def _get_up_alert(self):
        alert = AlertGenerator(self.event)
        alert.alert_type = 'bgpEstablished'
        return alert

    def _get_down_alert(self):
        alert = AlertGenerator(self.event)
        if self._is_peer_down():
            self._logger.info(
                "%s: peer is down, not posting bgp alert", self.get_target()
            )
            return
        return alert

    def _post_down_warning(self):
        pass

    def _is_peer_down(self):
        session = self.get_target()
        netbox = session.get_peer_as_netbox()
        if netbox:
            return not netbox.is_up()
