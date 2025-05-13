#
# Copyright (C) 2014 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Collect multicast statistics and send to Graphite"""

import time
import logging
from collections import Counter
from pprint import pformat

from twisted.internet import defer

from nav.ipdevpoll import Plugin
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import metric_path_for_multicast_usage
from nav.mibs.statistics_mib import StatisticsMib
from nav.enterprise.ids import VENDOR_ID_HEWLETT_PACKARD


class StatMulticast(Plugin):
    """Collects system statistics and pushes to Graphite"""

    @defer.inlineCallbacks
    def handle(self):
        vendor = self.netbox.type.get_enterprise_id() if self.netbox.type else None
        if vendor == VENDOR_ID_HEWLETT_PACKARD:
            yield self._collect_hp_multicast()

    @defer.inlineCallbacks
    def _collect_hp_multicast(self):
        timestamp = time.time()

        mib = StatisticsMib(self.agent)
        result = yield mib.get_ipv4_multicast_groups_per_port()

        if self._logger.isEnabledFor(logging.DEBUG):
            self._logger.debug("%s", pformat(result))

        if result:
            counts = self._count_ports_by_group(result)
            self._logger.debug("%r", counts)
            metrics = self._make_metrics_from_counts(counts, timestamp)
            if metrics:
                send_metrics(metrics)

    @staticmethod
    def _count_ports_by_group(report):
        """
        Counts the number of listening ports per multicast group.

        Only ports with apparent IGMP hosts are counted, not ports with
        apparent routers.
        """
        counter = Counter(r.group for r in report if r.access == "host")
        return counter

    def _make_metrics_from_counts(self, count_report, timestamp=None):
        timestamp = timestamp or time.time()
        return [
            (metric_path_for_multicast_usage(group, self.netbox), (timestamp, count))
            for group, count in count_report.items()
        ]
