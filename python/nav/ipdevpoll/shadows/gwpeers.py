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
from .netbox import Netbox


class GatewayPeerSessionManager(DefaultManager):
    _map = None

    def __init__(self, *args, **kwargs):
        super(GatewayPeerSessionManager, self).__init__(*args, **kwargs)
        self.netbox = self.containers.get(None, Netbox)
        self._sessions_to_keep = set()
        self._sessions_to_remove = set()

    def prepare(self):
        for session in self.get_managed():
            session.peer = str(session.peer)
        self._load_existing_sessions()
        self._map_known_sessions()
        self._map_unknown_sessions()

    def _load_existing_sessions(self):
        sessions = manage.GatewayPeerSession.objects
        sessions = sessions.filter(netbox=self.netbox.id)
        self._map = {(sess.protocol, str(sess.peer)): sess
                     for sess in sessions}

    def _map_known_sessions(self):
        for session in self.get_managed():
            key = (session.protocol, str(session.peer))
            if key in self._map:
                session.set_existing_model(self._map[key])
                self._sessions_to_keep.add(self._map[key])

    def _map_unknown_sessions(self):
        previous_sessions = set(self._map.values())
        self._sessions_to_remove = previous_sessions - self._sessions_to_keep

    def cleanup(self):
        if self._sessions_to_remove:
            self._logger.info("Removing these peering sessions, that seem to "
                              "have disappeared: %r", self._sessions_to_remove)
            for session in self._sessions_to_remove:
                session.delete()


class GatewayPeerSession(Shadow):
    """A GatewayPeerSession shadow class"""
    __shadowclass__ = manage.GatewayPeerSession
    _protocol_map = dict(manage.GatewayPeerSession.PROTOCOL_CHOICES)
    manager = GatewayPeerSessionManager

    def save(self, containers):
        model = self.get_existing_model(containers)
        if model:
            proto = self._protocol_map.get(self.protocol, None)
            if model.state != self.state:
                self._logger.info("%s STATE CHANGE DETECTED: %s -> %s",
                                  proto, model.state, self.state)
            if model.adminstatus != self.adminstatus:
                self._logger.info("%s ADMINSTATUS CHANGE DETECTED: %s -> %s",
                                  proto, model.adminstatus, self.adminstatus)

        return super(GatewayPeerSession, self).save(containers)
