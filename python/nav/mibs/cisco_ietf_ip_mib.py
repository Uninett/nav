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
"""Implements a MibRetriever for the CISCO-IETF-IP-MIB."""

from twisted.internet import defer

from nav.smidumps import get_mib
from nav.oids import OID
from .ip_mib import IpMib


class CiscoIetfIpMib(IpMib):
    """CISCO-IETF-IP-MIB is based on a a draft version of IETF's
    revised IP-MIB (with address type agnostic extensions).  Its
    structure is basically the same, with altered object names and
    ids.

    We try to avoid code redundancies by inheriting from the IpMib
    MibRetriever implementation, which was written using the revised
    IP-MIB.

    """

    mib = get_mib('CISCO-IETF-IP-MIB')

    @classmethod
    def address_index_to_ip(cls, index):
        """Convert a row index from cIpAddressTable to an IP object."""

        entry = cls.nodes['cIpAddressPfxOrigin']
        index = OID(index)
        if entry.oid.is_a_prefix_of(index):
            # Chop off the entry OID+column prefix
            index = OID(index.strip_prefix(entry.oid)[1:])

        return super(CiscoIetfIpMib, cls).address_index_to_ip(index)

    @classmethod
    def prefix_index_to_ip(cls, index, prefix_entry=None):
        """Convert a row index from cIpAddressPfxTable to an IP object."""

        entry = cls.nodes['cIpAddressPfxOrigin']
        stripped_index = OID(index).strip_prefix(entry.oid)

        return super(CiscoIetfIpMib, cls).prefix_index_to_ip(stripped_index)

    @defer.inlineCallbacks
    def get_ifindex_ip_mac_mappings(self):
        """Retrieve the layer 3->layer 2 address mappings of this device.

        Return value:
          A set of tuples: set([(ifindex, ip_address, mac_address), ...])
          ifindex will be an integer, ip_address will be an IPy.IP object and
          mac_address will be a string with a colon-separated hex representation
          of a MAC address.

        """
        mappings = yield self._get_ifindex_ip_mac_mappings(
            column='cInetNetToMediaPhysAddress'
        )

        return mappings

    @defer.inlineCallbacks
    def get_interface_addresses(self):
        """Retrieve the IP addresses and prefixes of interfaces.

        Return value:
          A set of tuples: set([(ifindex, ip_address, prefix_address), ...])
          ifindex will be an integer, ip_address and prefix_address will be
          IPy.IP objects.

        """
        addresses = yield self._get_interface_addresses(
            ifindex_column='cIpAddressIfIndex',
            prefix_column='cIpAddressPrefix',
            prefix_entry='cIpAddressPfxOrigin',
        )

        return addresses

    @staticmethod
    def _binary_mac_to_hex(mac):
        """Overrides parent implementation to work around a Cisco IOS issue
        with lengths of reported MAC addresses.

        """
        if mac and len(mac) > 6:
            mac = mac[:6]
        return IpMib._binary_mac_to_hex(mac)
