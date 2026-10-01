#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Vendor-neutral base for plugins collecting client authentication sessions
(802.1X, MAB, web auth) from switches.
"""

from dataclasses import dataclass
from typing import Optional

from nav.ipdevpoll import Plugin, db, shadows
from nav.ipdevpoll.shadows.access_session import make_session_key
from nav.models import manage

Session = manage.InterfaceAccessSession

MIN_VLAN, MAX_VLAN = 1, 4094


@dataclass(frozen=True, kw_only=True)
class CollectedSession:
    """An authentication session as collected from a device.

    `session_id` is the device's own identifier for the session, and is only
    used to derive a session key.  It must be stable for as long as the session
    lasts.  A device that reports at most one session per port and has no
    session identifier can pass a constant, such as b"0".

    `method`, `domain` and `status` use the choice values of the
    InterfaceAccessSession model.  `client_mac` is formatted as colon-separated
    lowercase hex, as produced by `nav.ipdevpoll.utils.binary_mac_to_hex()`.
    """

    ifindex: int
    session_id: bytes
    vlan_tag: Optional[int] = None
    method: str = Session.METHOD_UNKNOWN
    domain: str = Session.DOMAIN_UNKNOWN
    status: str = Session.STATUS_UNKNOWN
    client_mac: Optional[str] = None
    username: Optional[str] = None


class AccessSessionsPlugin(Plugin):
    """Keeps a snapshot of the authentication sessions on each switch port.

    Subclasses implement `collect_sessions()` for a specific vendor.  This
    class stores the result.  Sessions on interfaces NAV doesn't know are
    skipped, and sessions no longer reported are deleted.

    Each device must have at most one session source: the snapshot of a
    device is replaced by whatever the last run collected.  Subclasses must
    therefore restrict themselves to mutually exclusive vendors, using
    `RESTRICT_TO_VENDORS`.  Only the presence of a restriction is enforced;
    keeping the vendors of different subclasses apart is up to their authors.

    The client MAC address and user name are only stored when
    `collect_client_identity` is enabled in the `[access_sessions]` section of
    ipdevpoll.conf.  Otherwise they are set to NULL, which also clears any
    previously stored values.
    """

    collect_client_identity = False

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.RESTRICT_TO_VENDORS:
            raise TypeError(f"{cls.__name__} must set RESTRICT_TO_VENDORS")

    @classmethod
    def can_handle(cls, netbox: shadows.Netbox) -> bool:
        # The base class itself has no vendor restriction, and must never run
        return bool(cls.RESTRICT_TO_VENDORS) and super().can_handle(netbox)

    @classmethod
    def on_plugin_load(cls) -> None:
        from nav.ipdevpoll.config import ipdevpoll_conf

        cls.collect_client_identity = ipdevpoll_conf.getboolean(
            "access_sessions", "collect_client_identity", fallback=False
        )

    async def handle(self) -> None:
        sessions = await self.collect_sessions(self.collect_client_identity)
        self._logger.debug("found %d authentication sessions", len(sessions))

        # Ensures stale sessions are cleaned up even when none were found
        self.containers.add(shadows.InterfaceAccessSession)
        if not sessions:
            return

        ifindexes = {session.ifindex for session in sessions}
        known_ifindexes = await db.run_in_thread(self._get_known_ifindexes, ifindexes)
        netbox = self.containers.factory(None, shadows.Netbox)
        for session in sessions:
            if session.ifindex in known_ifindexes:
                self._store_session(netbox, session)
            else:
                self._logger.debug(
                    "ignoring session on unknown ifIndex %s", session.ifindex
                )

    async def collect_sessions(self, include_identity: bool) -> list[CollectedSession]:
        """Collects the authentication sessions currently active on the device.

        :param include_identity: Whether to collect the client MAC address and
                                 user name.  When false, implementations
                                 should not even retrieve them.
        """
        raise NotImplementedError

    def _get_known_ifindexes(self, ifindexes: set[int]) -> set[int]:
        return set(
            manage.Interface.objects.filter(
                netbox__id=self.netbox.id, ifindex__in=ifindexes
            ).values_list("ifindex", flat=True)
        )

    def _store_session(
        self, netbox: shadows.Netbox, collected: CollectedSession
    ) -> None:
        session_key = make_session_key(collected.session_id)
        session = self.containers.factory(
            (collected.ifindex, session_key), shadows.InterfaceAccessSession
        )
        session.interface = self.containers.factory(
            collected.ifindex, shadows.Interface
        )
        session.interface.netbox = netbox
        session.interface.ifindex = collected.ifindex
        session.session_key = session_key
        session.vlan_tag = valid_vlan_or_none(collected.vlan_tag)
        session.method = collected.method
        session.domain = collected.domain
        session.status = collected.status
        if self.collect_client_identity:
            session.client_mac = collected.client_mac
            session.username = collected.username
        else:
            session.client_mac = None
            session.username = None


def valid_vlan_or_none(vlan: object) -> Optional[int]:
    """Returns vlan if it is a valid VLAN tag, otherwise None.

    Devices commonly report 0 when no VLAN was assigned.
    """
    if isinstance(vlan, int) and MIN_VLAN <= vlan <= MAX_VLAN:
        return vlan
    return None
