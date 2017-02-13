#
# Copyright (C) 2017 UNINETT
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
"""Handling of gateway protocol state changes"""

from __future__ import absolute_import

from nav.ipdevpoll.storage import Shadow, DefaultManager
from nav.models import manage


class GatewayPeerSession(Shadow):
    """A GatewayPeerSession shadow class"""
    __shadowclass__ = manage.GatewayPeerSession
    __lookups__ = [('netbox', 'protocol', 'peer')]

    def save(self, containers):
        model = self.get_existing_model(containers)
        if model:
            if model.state != self.state:
                self._logger.info("%s STATE CHANGE DETECTED: %s -> %s",
                                  self.protocol, model.state, self.state)
        return super(GatewayPeerSession, self).save(containers)
