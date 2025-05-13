#
# Copyright (C) 2013 Uninett AS
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
# TODO: Add support for HOST-RESOURCES-MIB::hrSystemUptime as well
#
"""Collects uptime ticks and interprets discontinuities as cold boots"""

from datetime import timedelta, datetime

from twisted.internet.defer import inlineCallbacks

from nav.ipdevpoll import Plugin, shadows
from nav.ipdevpoll.timestamps import TimestampChecker

COLDBOOT_MAX_DELTA = 60 * 60  # seconds


class Uptime(Plugin):
    """Collects uptime ticks and discovers discontinuities in uptime data"""

    @inlineCallbacks
    def handle(self):
        is_deviant, new_upsince = yield self._get_timestamps()
        netbox = self.containers.factory(None, shadows.Netbox)
        if is_deviant:
            self._logger.warning("Detected possible coldboot at %s", new_upsince)

        if is_deviant or not self.netbox.up_since:
            self._logger.debug("setting new upsince: %s", new_upsince)
            netbox.up_since = new_upsince  # container netbox
            self.netbox.up_since = new_upsince  # input netbox

    @inlineCallbacks
    def _get_timestamps(self):
        stampcheck = TimestampChecker(self.agent, self.containers, "uptime")
        old_times = yield stampcheck.load()
        new_times = yield stampcheck.collect([])
        changed = old_times and stampcheck.is_changed(COLDBOOT_MAX_DELTA)
        self._logger.debug("uptime data (changed=%s): %r", changed, new_times)
        timestamp, ticks = new_times[0]
        upsince = get_upsince(timestamp, ticks)
        self._logger.debug(
            "last sysuptime reset/rollover reported by device: %s", upsince
        )
        stampcheck.save()
        return (changed, upsince)


def get_upsince(timestamp, ticks):
    """Calculates the datetime of a timestamp minus a ticks delta.

    :param timestamp: A number of seconds since the epoch.
    :param ticks: A number of SNMP timeticks / centiseconds.
    :returns: A datetime object representing the timestamp minus the ticks.

    """
    delta = timedelta(seconds=int(ticks / 100))
    sometime = datetime.fromtimestamp(timestamp)
    return sometime - delta
