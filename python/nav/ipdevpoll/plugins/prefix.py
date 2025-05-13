#
# Copyright (C) 2008-2012 Uninett AS
# Copyright (C) 2022-2023 Sikt
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
"""ipdevpoll plugin to poll IP prefix information.

This plugin will use the IF-MIB, IP-MIB, IPv6-MIB and
CISCO-IETF-IP-MIB to poll prefix information for both IPv4 and IPv6.

A revised version of the IP-MIB contains the IP-version-agnostic
ipAddressTable which is queried first, although not much equipment
supports this table yet.  It then falls back to the original IPv4-only
ipAddrTable, followed by the IPv6-MIB (which has been superseded by
the updated IP-MIB).  It also tries a Cisco proprietary
CISCO-IETF-IP-MIB, which is based on a draft that later became the
revised IP-MIB.

An interface with an IP address whose name matches the VLAN_PATTERN
will cause the corresponding prefix to be associated with the VLAN id
parsed from the interface name.  Not all dot1q enabled routers name
their interfaces like this, but routing switches from several vendors
do.

"""

import re
import logging

from twisted.internet import defer, error

from IPy import IP

from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib
from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib
from nav.mibs.cisco_ietf_ip_mib import CiscoIetfIpMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import shadows

VLAN_PATTERN = re.compile(
    r"(Vl(an)?|irb\.|reth\d+\.|bond\d+\.)(?P<vlan>\d+)",
    re.IGNORECASE,
)


class Prefix(Plugin):
    """
    ipdevpoll-plugin for collecting prefix information from monitored
    equipment.
    """

    @classmethod
    def on_plugin_load(cls):
        from nav.ipdevpoll.config import ipdevpoll_conf

        cls.ignored_prefixes = get_ignored_prefixes(ipdevpoll_conf)

    @defer.inlineCallbacks
    def handle(self):
        self._logger.debug("Collecting prefixes")
        netbox = self.containers.factory(None, shadows.Netbox)

        ipmib = IpMib(self.agent)
        ciscoip = CiscoIetfIpMib(self.agent)
        ipv6mib = Ipv6Mib(self.agent)

        # Retrieve interface names and keep those who match a VLAN
        # naming pattern
        vlan_interfaces = yield self.get_vlan_interfaces()
        ifc_aliases = yield self._get_ifc_aliases()

        # Traverse address tables from IP-MIB, IPV6-MIB and
        # CISCO-IETF-IP-MIB in that order.
        addresses = set()
        for mib in ipmib, ipv6mib, ciscoip:
            self._logger.debug("Trying address tables from %s", mib.mib['moduleName'])
            df = mib.get_interface_addresses()
            # Special case; some devices will time out while building a bulk
            # response outside our scope when it has no proprietary MIB support
            if mib != ipmib:
                df.addErrback(self._ignore_timeout, set())
            df.addErrback(self._ignore_index_exceptions, mib)
            new_addresses = yield df
            self._logger.debug(
                "Found %d addresses in %s: %r",
                len(new_addresses),
                mib.mib['moduleName'],
                new_addresses,
            )
            addresses.update(new_addresses)

        adminup_ifcs = yield self._get_adminup_ifcs()
        for ifindex, ip, prefix in addresses:
            if ifindex not in adminup_ifcs:
                self._logger.debug(
                    "ignoring collected address %s on admDown ifindex %s", ip, ifindex
                )
                continue
            if self._prefix_should_be_ignored(prefix):
                self._logger.debug("ignoring prefix %s as configured", prefix)
                continue
            self.create_containers(
                netbox, ifindex, prefix, ip, vlan_interfaces, ifc_aliases
            )

    def _get_ifc_aliases(self):
        return IfMib(self.agent).get_ifaliases()

    def _ignore_index_exceptions(self, failure, mib):
        failure.trap(IndexToIpException)
        self._logger.warning(
            "device has strange SNMP implementation of %s; "
            "ignoring retrieved IP address data: %s",
            mib.mib['moduleName'],
            failure.getErrorMessage(),
        )
        return set()

    @defer.inlineCallbacks
    def _get_adminup_ifcs(self):
        ifmib = IfMib(self.agent)
        statuses = yield ifmib.get_admin_status()
        result = set(ifindex for ifindex, status in statuses.items() if status == 'up')
        return result

    def create_containers(
        self, netbox, ifindex, net_prefix, ip, vlan_interfaces, ifc_aliases=None
    ):
        """
        Utitilty method for creating the shadow-objects
        """
        interface = self.containers.factory(ifindex, shadows.Interface)
        interface.ifindex = ifindex
        if ifc_aliases and ifc_aliases.get(ifindex, None):
            interface.ifalias = ifc_aliases[ifindex]
        interface.netbox = netbox

        # No use in adding the GwPortPrefix unless we actually found a prefix
        if net_prefix:
            port_prefix = self.containers.factory(ip, shadows.GwPortPrefix)
            port_prefix.interface = interface
            port_prefix.gw_ip = str(ip)

            prefix = self.containers.factory(net_prefix, shadows.Prefix)
            prefix.net_address = str(net_prefix)
            # Host masks aren't included when IPy converts to string
            if '/' not in prefix.net_address:
                prefix.net_address += "/%s" % net_prefix.prefixlen()
            port_prefix.prefix = prefix

            # Always associate prefix with a VLAN record, but set a
            # VLAN number if we can.
            vlan = self.containers.factory(ifindex, shadows.Vlan)
            if ifindex in vlan_interfaces:
                vlan.vlan = vlan_interfaces[ifindex]

            prefix.vlan = vlan

    @defer.inlineCallbacks
    def get_vlan_interfaces(self):
        """Get all virtual VLAN interfaces.

        Any interface whose ifName matches the VLAN_PATTERN regexp
        will be included in the result.

        Return value:

          A deferred whose result is a dictionary: { ifindex: vlan }

        """
        ifmib = IfMib(self.agent)
        df = ifmib.retrieve_column('ifName')
        df.addCallback(reduce_index)
        interfaces = yield df

        vlan_ifs = {}
        for ifindex, ifname in interfaces.items():
            match = VLAN_PATTERN.match(ifname)
            if match:
                vlan = int(match.group('vlan'))
                vlan_ifs[ifindex] = vlan

        return vlan_ifs

    def _ignore_timeout(self, failure, result=None):
        """Ignores a TimeoutError in an errback chain.

        The result argument will be returned, and there injected into the
        regular callback chain.

        """
        failure.trap(error.TimeoutError, defer.TimeoutError)
        self._logger.debug("request timed out, ignoring and moving on...")
        return result

    def _prefix_should_be_ignored(self, prefix):
        if prefix is None:
            return False

        return any(ignored.matches(prefix) for ignored in self.ignored_prefixes)


def get_ignored_prefixes(config):
    """Returns a list of ignored prefixes from a ConfigParser instance"""
    if config is not None:
        raw_string = config.get('prefix', 'ignored', fallback='')
    else:
        return []
    items = raw_string.split(',')
    prefixes = [_convert_string_to_prefix(i) for i in items]
    return [prefix for prefix in prefixes if prefix is not None]


def _convert_string_to_prefix(string):
    try:
        return IgnoredPrefix(string)
    except ValueError:
        logging.getLogger(__name__).error(
            "Ignoring invalid prefix in ignore list: %s", string
        )


class IgnoredPrefix(IP):
    """An ignored prefix.

    May match every contained prefix, or just the identical prefix, according
    to the input syntax. If no match operator is present, the "contained
    within or equals" operator is assumed (since that was the default behavior
    of bare addresses before operators were introduced).

    Examples::
    >>> IgnoredPrefix('192.168.1.0/24').matches('192.168.1.128/25')
    True
    >>> IgnoredPrefix('<<=192.168.1.0/24').matches('192.168.1.128/25')
    True
    >>> IgnoredPrefix('=192.168.1.0/24').matches('192.168.1.0/24')
    True

    """

    EQUALS_OPERATOR = '='
    CONTAINED_IN_OPERATOR = '<<='
    OPERATORS = (EQUALS_OPERATOR, CONTAINED_IN_OPERATOR)

    DEFAULT_OPERATOR = CONTAINED_IN_OPERATOR
    match_operator = DEFAULT_OPERATOR

    def __init__(self, string):
        string = string.strip()

        for oper in self.OPERATORS:
            if string.startswith(oper):
                self.match_operator = oper
                string = string.removeprefix(oper)
                break

        IP.__init__(self, string)  # stupid old-style class implementation!

    def matches(self, prefix):
        """
        Returns True if prefix matches this ignored prefix, using the
        matching operator specified for this instance.
        """
        assert self.match_operator in self.OPERATORS

        if self.match_operator == self.EQUALS_OPERATOR:
            return IP(prefix) == self
        elif self.match_operator == self.CONTAINED_IN_OPERATOR:
            return IP(prefix) in self
        else:
            return NotImplementedError
