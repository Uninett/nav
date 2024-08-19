#
# Copyright (C) 2016 Uninett AS
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
import logging
from collections import defaultdict
from twisted.internet.defer import inlineCallbacks

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows
from nav.mibs.ieee8023_lag_mib import IEEE8023LagMib
from nav.mibs.if_mib import IfMib


class LinkAggregate(Plugin):
    """Collects information about link aggregation"""

    def __init__(self, *args, **kwargs):
        super(LinkAggregate, self).__init__(*args, **kwargs)
        self.ifmib = IfMib(self.agent)
        self.lagmib = IEEE8023LagMib(self.agent)

    @inlineCallbacks
    def handle(self):
        self._logger.debug("Collecting link aggregations")
        result = yield self.lagmib.retrieve_aggregations_by_operational_key()
        aggregates = yield self._convert_to_interfaces(result)
        self._log_aggregates(aggregates)
        self._create_aggregate_containers(aggregates)

    @inlineCallbacks
    def _convert_to_interfaces(self, aggregatedict):
        result = []
        for aggregator_idx, aggregates in aggregatedict.items():
            aggregator = yield self._get_interface(aggregator_idx)
            for if_idx in aggregates:
                interface = yield self._get_interface(if_idx)
                result.append((interface, aggregator))
        return result

    @inlineCallbacks
    def _get_interface(self, ifindex):
        ifc = self.containers.factory(ifindex, shadows.Interface, ifindex=ifindex)
        if not ifc.ifname:
            # In case no other plugins ran before us to collect this:
            self._logger.debug("retrieving ifName.%s", ifindex)
            ifc.ifname = yield self.ifmib.retrieve_column_by_index('ifName', (ifindex,))
        return ifc

    def _log_aggregates(self, aggregates):
        if not self._logger.isEnabledFor(logging.DEBUG):
            return

        aggr = defaultdict(list)
        for ifc, aggregator in aggregates:
            aggr[aggregator.ifname].append(ifc.ifname)

        for aggregator, ports in aggr.items():
            self._logger.debug(
                "%s aggregates these ports: %s", aggregator, ', '.join(ports)
            )

    def _create_aggregate_containers(self, aggregates):
        for interface, aggregator in aggregates:
            key = aggregator.ifindex, interface.ifindex
            aggregate = self.containers.factory(key, shadows.InterfaceAggregate)
            aggregate.aggregator = aggregator
            aggregate.interface = interface
