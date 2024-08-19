#
# Copyright (C) 2009-2011 Uninett AS
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
"""An IPV6-MIB MibRetriever.

Although IPV6-MIB has been obsoleted by a revised version of IP-MIB,
some vendors still only provide IPv6 data in this MIB.

"""

from twisted.internet import defer

from nav.ipdevpoll.utils import binary_mac_to_hex
from nav.smidumps import get_mib
from . import mibretriever
from . import ip_mib


class Ipv6Mib(mibretriever.MibRetriever):
    """A MibRetriever for the deprecated IPv6-MIB"""

    mib = get_mib('IPV6-MIB')

    @staticmethod
    def ipv6address_to_ip(oid):
        """Convert an OID tuple to an IPy.IP object.

        The OID tuple syntex is expected to follow the Ipv6Address
        textual convention defined in IPV6-TC.

        Example:

        >>> oid = (254,128,0,0,0,0,0,0,2,28,46,255,254,233,228,0)
        >>> inetaddress_to_ip(oid)
        IP('fe80::21c:2eff:fee9:e400')
        >>>

        """
        # We convert the oid's syntax into
        # InetAddressType+InetAdddress and push it through the already
        # working mechanism in the ip_mib module.
        ipv6_type = 2
        length = 16
        if len(oid) == 17 and oid[0] == length:
            # need to work around some devices that don't implement the
            # IPV6-TC properly
            converted_oid = (ipv6_type,) + oid
        else:
            converted_oid = (ipv6_type, length) + oid
        return ip_mib.IpMib.inetaddress_to_ip(converted_oid)

    @defer.inlineCallbacks
    def get_ifindex_ip_mac_mappings(self):
        """Retrieve the IPv6->MAC address mappings of this device.

        Return value:
          A set of tuples: set([(ifindex, ip_address, mac_address), ...])
          ifindex will be an integer, ip_address will be an IPy.IP object and
          mac_address will be a string with a colon-separated hex representation
          of a MAC address.

        """
        column = 'ipv6NetToMediaPhysAddress'
        ipv6_phys_addrs = yield self.retrieve_column(column)

        mappings = set()

        for row_index, phys_address in ipv6_phys_addrs.items():
            ifindex = row_index[0]
            ipv6_address = row_index[1:]
            ip = Ipv6Mib.ipv6address_to_ip(ipv6_address)
            mac = binary_mac_to_hex(phys_address)

            row = (ifindex, ip, mac)
            mappings.add(row)
        self._logger.debug(
            "ip/mac pairs: Got %d rows from %s", len(ipv6_phys_addrs), column
        )
        return mappings

    @defer.inlineCallbacks
    def get_interface_addresses(self):
        """Retrieve the IPv6 addresses and prefixes of interfaces.

        Return value:
          A set of tuples: set([(ifindex, ip_address, prefix_address), ...])
          ifindex will be an integer, ip_address and prefix_address will be
          IPy.IP objects.

        """
        prefixlen_column = 'ipv6AddrPfxLength'
        ipv6_addrs = yield self.retrieve_column(prefixlen_column)

        addresses = set()

        for row_index, prefixlen in ipv6_addrs.items():
            ifindex = row_index[0]
            ipv6_address = row_index[1:]
            ip = Ipv6Mib.ipv6address_to_ip(ipv6_address)

            prefix = ip.make_net(prefixlen)

            row = (ifindex, ip, prefix)
            addresses.add(row)
        self._logger.debug(
            "interface addresses: Got %d rows from %s",
            len(ipv6_addrs),
            prefixlen_column,
        )

        return addresses
