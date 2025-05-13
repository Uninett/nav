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
"""Handling of gateway protocol state changes"""

from functools import partial

from django.db import transaction

from nav.event2 import EventFactory
from nav.ipdevpoll.storage import Shadow, DefaultManager
from nav.models import manage
from .netbox import Netbox


EVENT = EventFactory(
    source='ipdevpoll',
    target='eventEngine',
    event_type='bgpState',
    start_type='bgpDown',
    end_type='bgpEstablished',
)


class GatewayPeerSessionManager(DefaultManager):
    """Manager for GatewayPeerSession objects"""

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
        self._map = {(sess.protocol, str(sess.peer)): sess for sess in sessions}

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
            self._logger.info(
                "Removing these peering sessions, that seem to have disappeared: %r",
                self._sessions_to_remove,
            )
            for session in self._sessions_to_remove:
                session.delete()


class GatewayPeerSession(Shadow):
    """A GatewayPeerSession shadow class"""

    __shadowclass__ = manage.GatewayPeerSession
    _protocol_map = dict(manage.GatewayPeerSession.PROTOCOL_CHOICES)
    manager = GatewayPeerSessionManager

    def save(self, containers):
        self._verify_state_changes(containers)
        return super(GatewayPeerSession, self).save(containers)

    def _verify_state_changes(self, containers):
        """
        Verifies potential state changes and posts a single alert if the
        state change(s) warrants it.

        If admin status has changed, primarily an event about that. If not,
        post events if session state switches between 'established' and
        non-established states.

        """
        if not should_alert_on_ibgp() and self.is_ibgp():
            return  # GTFO

        self._log_all_state_changes(containers)
        model = self.get_existing_model(containers)
        if not model:
            return

        if model.adminstatus != self.adminstatus:
            new_alert = self.adminstatus in ('stop', 'halted')
            self._make_bgpstate_event(start=new_alert, is_adminstatus=True)
            return

        states = set((model.state, self.state))
        if len(states) > 1 and 'established' in states:
            new_alert = self.state != 'established'
            self._make_bgpstate_event(start=new_alert)

    def _log_all_state_changes(self, containers):
        model = self.get_existing_model(containers)
        if not model:
            return
        proto = self._protocol_map.get(self.protocol, None)
        peerid = self._get_peer_id()

        if model.adminstatus != self.adminstatus:
            self._logger.debug(
                "%s %s adminstatus change detected: %s -> %s",
                proto,
                peerid,
                model.adminstatus,
                self.adminstatus,
            )
        if model.state != self.state:
            self._logger.debug(
                "%s %s state change detected: %s -> %s",
                proto,
                peerid,
                model.state,
                self.state,
            )

    @transaction.atomic
    def _make_bgpstate_event(self, start=True, is_adminstatus=False):
        model = self.get_existing_model()
        peername = self._get_peer_name() or str(model.peer)
        peerid = self._get_peer_id()
        varmap = {
            'peer': str(model.peer),
            'peername': peername,
            'state': self.state,
            'adminstatus': self.adminstatus,
        }
        event = EVENT.start if start else EVENT.end
        if start and is_adminstatus:
            event = partial(event, alert_type='bgpAdmDown')
        event = event(netbox=self.netbox.id, subid=model.id, varmap=varmap)

        proto = self._protocol_map.get(self.protocol, None)
        self._logger.info(
            "dispatching event (%s) for %s %s state change from %s to %s",
            event.varmap['alerttype'],
            proto,
            peerid,
            model.state,
            self.state,
        )
        event.save()

    def _get_peer_name(self):
        if not self.peer:
            return

        if not getattr(self, '_peername', None):
            try:
                peers = manage.Netbox.objects.filter(ip=self.peer)
                self._peername = peers.values_list('sysname', flat=1)[0]
            except (IndexError, AttributeError):
                self._peername = None

        return self._peername

    def _get_peer_id(self):
        peername = self._get_peer_name()
        if peername:
            return "{} ({})".format(self.peer, peername)
        else:
            return self.peer

    def is_ibgp(self):
        """Returns True if this is an iBGP session"""
        return self.local_as == self.remote_as


def should_alert_on_ibgp():
    """Returns the value of the IBGP alert option of ipdevpoll config"""
    from nav.ipdevpoll.config import ipdevpoll_conf as conf

    default = True
    alert_ibgp = (
        conf.getboolean('bgp', 'alert_ibgp')
        if conf.has_option('bgp', 'alert_ibgp')
        else default
    )
    return alert_ibgp
