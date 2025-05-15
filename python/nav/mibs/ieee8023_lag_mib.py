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
""" "A MibRetriever to retrieve IEEE 802.3ad info from the IEEE8023-LAG-MIB"""

from collections import defaultdict
from twisted.internet.defer import inlineCallbacks
from nav.smidumps import get_mib
from nav.mibs import mibretriever, reduce_index


class IEEE8023LagMib(mibretriever.MibRetriever):
    """ "A MibRetriever for handling IEEE8023-LAG-MIB"""

    mib = get_mib('IEEE8023-LAG-MIB')

    @inlineCallbacks
    def retrieve_selected_aggregators(self):
        """
        Retrieves a dict of ifIndexes of aggregation ports and the ifIndex of
        their selected aggregation port, if one is selected.

        :returns: { aggregation_ifindex: aggregator_ifindex, ... }
        """
        result = yield self.retrieve_column('dot3adAggPortSelectedAggID').addCallback(
            reduce_index
        )
        return {
            port: aggregator for port, aggregator in result.items() if aggregator != 0
        }

    @inlineCallbacks
    def retrieve_attached_aggregators(self):
        """
        Retrieves a dict of ifIndexes of aggregation ports and the ifIndex of
        their attached aggregation port, if one is attached.

        :returns: { aggregation_ifindex: aggregator_ifindex, ... }
        """
        result = yield self.retrieve_column('dot3adAggPortAttachedAggID').addCallback(
            reduce_index
        )
        return {
            port: aggregator for port, aggregator in result.items() if aggregator != 0
        }

    @inlineCallbacks
    def retrieve_aggregations_by_operational_key(self):
        """
        Retrieves a dict where the keys are the ifIndexes of aggregators,
        and the values are lists of ifIndexes of aggregation ports with the
        corresponding operational key (regardless of their current status).

        :returns: { aggregation_ifindex: aggregator_ifindex, ... }
        """
        aggregators = yield self.retrieve_column('dot3adAggActorOperKey').addCallback(
            reduce_index
        )
        aggregations = yield self.retrieve_column(
            'dot3adAggPortActorOperKey'
        ).addCallback(reduce_index)

        by_opervalue = defaultdict(list)
        for ifindex, opervalue in aggregations.items():
            by_opervalue[opervalue].append(ifindex)

        result = {
            ifindex: by_opervalue[opervalue]
            for ifindex, opervalue in aggregators.items()
            if opervalue in by_opervalue
        }

        return result
