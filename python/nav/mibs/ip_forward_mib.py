#
# Copyright (C) 2016 Uninett AS
# Copyright (C) 2022 Sikt
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
"""A MibRetriever implementation for IP-FORWARD-MIB"""

from collections import defaultdict
from itertools import chain
from collections import namedtuple

from twisted.internet.defer import inlineCallbacks

from nav.smidumps import get_mib
from nav.oidparsers import consume
from nav.oidparsers import InetPrefix, ObjectIdentifier, TypedInetAddress
from . import mibretriever

# Extracted from IANA-RPROTO-MIB::IANAipRouteProtocol, revision 200009260000Z
IANA_IP_ROUTE_PROTOCOLS = {
    1: 'other',
    2: 'local',
    3: 'netmgmt',
    4: 'icmp',
    5: 'egp',
    6: 'ggp',
    7: 'hello',
    8: 'rip',
    9: 'isIs',
    10: 'esIs',
    11: 'ciscoIgrp',
    12: 'bbnSpfIgp',
    13: 'ospf',
    14: 'bgp',
    15: 'idpr',
    16: 'ciscoEigrp',
    17: 'dvmrp',
}

CidrRouteEntry = namedtuple(
    'CidrRouteEntry', ('index', 'destination', 'policy', 'nexthop')
)


class IpForwardMib(mibretriever.MibRetriever):
    """A MibRetriever implementation for IP-FORWARD-MIB"""

    mib = get_mib('IP-FORWARD-MIB')

    @inlineCallbacks
    def get_routes(self, protocols=None):
        """
        Returns the index of every entry in the routing table that matches any
        of the specific protocols. If the protocols argument is omitted, a
        dictionary of routes by protocols, {proto: [route1, route2, ...], ...}
        is returned.

        :param protocols: A list of protocol names.

        """
        protos = yield self.retrieve_column('inetCidrRouteProto')

        by_proto = defaultdict(list)
        for index, proto in protos.items():
            name = IANA_IP_ROUTE_PROTOCOLS.get(proto, proto)
            by_proto[name].append(index)

        if protocols:
            result = chain(*[by_proto.get(proto, []) for proto in protocols])
            return list(result)
        else:
            return dict(by_proto)

    @inlineCallbacks
    def get_decoded_routes(self, protocols=None):
        """
        Returns a CidrRouteEntry tuple from every parseable entry in the routing
        table that matches any of the specific protocols. If the protocols
        argument is omitted, a dictionary of routes by protocols, {proto:
        [route1, route2, ...], ...} is returned.

        Non-parseable routes are ignored and removed.

        :param protocols: A list of protocol names.

        """

        def decode(index):
            try:
                return decode_route_entry(index)
            except ValueError as error:
                self._logger.debug("Route index was unparseable (%s): %r", error, index)
                return None

        result = yield self.get_routes(protocols)
        if protocols:
            result = [
                entry for entry in (decode_route_entry(r) for r in result) if entry
            ]
        else:
            for proto in result:
                result[proto] = [
                    entry
                    for entry in (decode_route_entry(r) for r in result[proto])
                    if entry
                ]
        return result

    def get_cidr_route_column(self, column, index):
        """Retrieves the value of a specific column for a given route index"""
        if not column.startswith('inetCidrRoute'):
            column = 'inetCidrRoute' + column
        return self.retrieve_column_by_index(column, index)


def decode_route_entry(index):
    """Decodes the important bits of an inetCidrRouteTable row index.

    :rtype: CidrRouteEntry

    """
    destination, policy, nexthop = consume(
        index, InetPrefix, ObjectIdentifier, TypedInetAddress
    )
    return CidrRouteEntry(index, destination, policy, nexthop)
