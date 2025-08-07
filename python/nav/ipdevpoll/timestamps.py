#
# Copyright (C) 2012-2015, 2019 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""SNMP timestamps and sysUpTime comparisons"""

import json

from twisted.internet import defer

from nav.mibs.snmpv2_mib import Snmpv2Mib

from nav.ipdevpoll import db, shadows
from nav.ipdevpoll.log import ContextLogger
from nav.models import manage

INFO_KEY_NAME = 'poll_times'


class TimestampChecker(object):
    """Generic handling of SNMP time stamp checking.

    Various MIBs provide last-updated timestamps for potentially large
    tables. These timestamps are usually reported as the value of sysUpTime
    when the last table modification was made.

    A manager should collect such a timestamp before collecting a large
    table. If the timestamp is unchanged on the next collection run, then it
    needn't waste time collecting the unchanged table over again.

    Some tables will have a timestamp of 0, meaning it was last changed at the
    time the SNMP agent was initialized. If the SNMP agent has been
    re-initialized or the device rebooted, the timestamp may still be 0, while
    the table contents have changed.  Therefore, the manager should check for
    deviations in the expected sysUpTime value - if it appears the device has
    restarted, it's time to collect the full table again, to be on the safe
    side.

    This class provides re-usable mechanisms for doing these operations in an
    ipdevpoll context.  It can perform the sysUpTime collection and receive
    the results of other timestamp query results, persist these to the NAVdb
    and/or compare them with previously persisted values to determine whether
    table re-collection should occur.

    """

    _logger = ContextLogger()

    def __init__(self, agent, containers, var_name):
        self._logger
        self.agent = agent
        self.snmpv2mib = Snmpv2Mib(agent)
        self.containers = containers
        self.var_name = var_name
        self.collected_times = None
        self.loaded_times = None

    @defer.inlineCallbacks
    def collect(self, collectors):
        """Collects timestamp results in parallel, using a DeferredList.

        :param collectors: A list of deferreds to wait for - the deferreds
                           should return integer results.

        """
        result = yield defer.DeferredList(
            [self.snmpv2mib.get_timestamp_and_uptime()] + list(collectors)
        )
        tup = []
        for success, value in result:
            if success:
                tup.append(value)
            else:
                value.raiseException()
        self.collected_times = tuple(tup)
        return self.collected_times

    @defer.inlineCallbacks
    def load(self):
        """Loads existing timestamps from db"""

        def _deserialize():
            try:
                info = manage.NetboxInfo.objects.get(
                    netbox__id=self._get_netbox().id,
                    key=INFO_KEY_NAME,
                    variable=self.var_name,
                )
            except manage.NetboxInfo.DoesNotExist:
                return None
            try:
                return json.loads(info.value)
            except (
                AttributeError,
                json.JSONDecodeError,
                UnicodeDecodeError,
                TypeError,
            ):
                return None

        self.loaded_times = yield db.run_in_thread(_deserialize)
        return self.loaded_times

    def save(self):
        """Saves timestamps to a ContainerRepository"""
        netbox = self._get_netbox()
        info = self.containers.factory(
            (INFO_KEY_NAME, self.var_name), shadows.NetboxInfo
        )
        info.netbox = netbox
        info.key = INFO_KEY_NAME
        info.variable = self.var_name
        info.value = json.dumps(self.collected_times)

    def _get_netbox(self):
        return self.containers.factory(None, shadows.Netbox)

    def is_changed(self, max_deviation=60):
        """Verifies whether any timestamps have changed.

        :param max_deviation: Accepted sysUpTime deviation before a device is
                              considered to have rebooted, in number of
                              seconds.

        :returns: True if any of the collected timestamps are different from
                  the loaded ones, or if a discontinuity in sysUpTime (aka a
                  reboot) is detected.

        """
        if not self.loaded_times:
            self._logger.debug("%r: no previous collection times found", self.var_name)
            return True

        old_uptime, old_times = (self.loaded_times[0], self.loaded_times[1:])
        new_uptime, new_times = (self.collected_times[0], self.collected_times[1:])
        uptime_deviation = self.snmpv2mib.get_uptime_deviation(old_uptime, new_uptime)

        if None in new_times:
            self._logger.debug(
                "%r: None in timestamp list: %r", self.var_name, new_times
            )
            return True
        if uptime_deviation is None:
            self._logger.debug(
                "%r: unable to calculate uptime deviation for old/new: %r/%r",
                self.var_name,
                old_times,
                new_times,
            )
            return True
        if list(old_times) != list(new_times):
            self._logger.debug(
                "%r: timestamps have changed: %r / %r",
                self.var_name,
                old_times,
                new_times,
            )
            return True
        elif abs(uptime_deviation) > max_deviation:
            self._logger.debug(
                "%r: sysUpTime deviation detected, possible reboot", self.var_name
            )
            return True
        else:
            self._logger.debug(
                "%r: timestamps appear unchanged since last run", self.var_name
            )
            return False
