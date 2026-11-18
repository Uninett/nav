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
"""Shadow for client authentication sessions on interfaces"""

from django.utils.crypto import salted_hmac

from nav.ipdevpoll.storage import Shadow
from nav.models import manage

from .netbox import Netbox

SESSION_KEY_SALT = "nav.ipdevpoll.access_session"


def make_session_key(session_id: bytes) -> str:
    """Returns a stable key for a switch's own session identifier.

    The raw identifier may also appear in RADIUS logs, so it is never stored.
    The key is an HMAC keyed with NAV's SECRET_KEY instead, which can't be
    matched against those logs without knowing the secret.  Changing
    SECRET_KEY changes every key, so all sessions look new on the next poll.
    """
    return salted_hmac(SESSION_KEY_SALT, session_id, algorithm="sha256").hexdigest()


class InterfaceAccessSession(Shadow):
    __shadowclass__ = manage.InterfaceAccessSession
    __lookups__ = [("interface", "session_key")]

    @classmethod
    def cleanup_after_save(cls, containers):
        """Deletes this netbox' sessions that weren't collected in this run"""
        found = [session.id for session in containers[cls].values()]
        netbox = containers.get(None, Netbox)
        manage.InterfaceAccessSession.objects.filter(
            interface__netbox=netbox.id
        ).exclude(pk__in=found).delete()
