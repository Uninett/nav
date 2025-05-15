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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""ipdevpoll plugin to find and store static routes from routing tables"""

import configparser

from twisted.internet import defer

from nav.ipdevpoll.shadows import Prefix, Vlan, NetType
from nav.mibs.ip_forward_mib import IpForwardMib
from nav.mibs.if_mib import IfMib

from nav.ipdevpoll import Plugin
from .prefix import get_ignored_prefixes

WANTED_PROTOCOLS = ("local", "netmgmt")


class StaticRoutes(Plugin):
    """
    Collects the entire routing table to select only static routes
    """

    ignored_prefixes = ()

    @classmethod
    def on_plugin_load(cls):
        from nav.ipdevpoll.config import ipdevpoll_conf

        cls.ignored_prefixes = get_ignored_prefixes(ipdevpoll_conf)
        cls.throttle_delay = get_throttle_delay(ipdevpoll_conf)

    @classmethod
    def can_handle(cls, netbox):
        """This will only be useful on layer 3 devices, i.e. GW/GSW devices."""
        daddy_says_ok = super(StaticRoutes, cls).can_handle(netbox)
        return daddy_says_ok and netbox.category.id in ('GW', 'GSW')

    @defer.inlineCallbacks
    def handle(self):
        """Initiates throttled collection of routing table"""
        orig_delay = self.agent.throttle_delay
        self.agent.throttle_delay = self.throttle_delay
        try:
            yield self.collect_routes()
        finally:
            self.agent.throttle_delay = orig_delay

    @defer.inlineCallbacks
    def collect_routes(self):
        """
        Collects the routing table, filters out what we consider to be static
        routes worthy of storage in NAV, and ensure storage as prefixes.

        """
        mib = IpForwardMib(self.agent)
        ifmib = IfMib(self.agent)

        routes = yield mib.get_decoded_routes(protocols=WANTED_PROTOCOLS)
        filtered = [r for r in routes if self.is_wanted_route(r)]

        self._logger.debug(
            "%d of %d collected routes are static candidates",
            len(filtered),
            len(routes),
        )
        self._logger.debug(
            "collected destinations: %r", [r.destination for r in filtered]
        )

        for route in filtered:
            ifindex = yield mib.get_cidr_route_column('IfIndex', route.index)
            alias = None
            if ifindex:
                alias = yield ifmib.retrieve_column_by_index('ifAlias', (ifindex,))
            self.route_to_containers(route, descr=alias)

        Prefix.add_static_routes_sentinel(self.containers)

    def route_to_containers(self, route, descr=None):
        """Helper method to create container objects for db persistence"""
        if self.containers.get(route.destination, Prefix):
            self._logger.debug(
                "ignoring static route for %s, prefix already exists", route.destination
            )
            return

        vlan = self.containers.factory(route.destination, Vlan)
        vlan.net_type = NetType.get('static')
        sysname = self.netbox.sysname.split('.')[0]
        vlan.net_ident = "{},{}".format(sysname, route.nexthop)
        if descr:
            vlan.description = descr

        prefix = self.containers.factory(route.destination, Prefix)
        prefix.net_address = str(route.destination)
        prefix.vlan = vlan

    @classmethod
    def is_wanted_route(cls, route):
        """Returns True if this CidrRouteEntry is interesting to NAV.

        :type route: CidrRouteEntry

        """
        dest = route.destination
        if dest.version() == 4 and dest.prefixlen() == 32:
            return False  # no host routes, please
        if dest.version() == 6 and dest.prefixlen() == 128:
            return False  # no host routes, please
        if route.nexthop is None:
            return False  # only care about routes that have a nexthop
        for ignored in cls.ignored_prefixes:
            if ignored.matches(dest):
                return False  # explicitly ignored by config
        return True


def get_throttle_delay(config):
    """Returns a throttle delay value from a ConfigParser instance"""
    try:
        return config.getfloat('staticroutes', 'throttle-delay')
    except configparser.Error:
        return 0.0
