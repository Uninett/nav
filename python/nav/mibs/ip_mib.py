# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 Uninett AS
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
"""MibRetriever implementation for IP-MIB"""

from twisted.internet.defer import inlineCallbacks

from nav.oids import OID
from nav.oidparsers import IPV4_ID, IPV6_ID, oid_to_ipv6, oid_to_ipv4
from nav.ipdevpoll.utils import binary_mac_to_hex
from nav.smidumps import get_mib
from . import mibretriever

IP_IN_OCTETS = 'ipIfStatsHCInOctets'
IP_OUT_OCTETS = 'ipIfStatsHCOutOctets'


class IpMib(mibretriever.MibRetriever):
    """MibRetriever implementation for IP-MIB"""

    mib = get_mib('IP-MIB')

    @staticmethod
    def inetaddress_to_ip(oid):
        """Convert an OID tuple to an IPy.IP object.

        The OID is interpreted as a combination of the textual
        conventions InetAddressType and InetAddress defined in
        INET-ADDRESS-MIB.

        Only the ipv4 and ipv6 address types are understood.  Any
        other type encountered will result in a None value returned.

        Example:

        >>> oid = (2,16,254,128,0,0,0,0,0,0,2,28,46,255,254,233,228,0)
        >>> inetaddress_to_ip(oid)
        IP('fe80::21c:2eff:fee9:e400')
        >>>


        TODO: as the mibretriever system evolves to allow
        interdependencies, the parsing of the InetAddress TC should be
        in a separate inet_address_mib module.

        """
        addr_type = oid[0]
        addr = oid[1:]

        if addr_type == IPV4_ID:
            expected_len = 4
            converter = oid_to_ipv4
        elif addr_type == IPV6_ID:
            expected_len = 16
            converter = oid_to_ipv6
        else:
            # Unknown address type
            return

        # this mucking about with address lengths are due to the technical
        # issue described in LP#777821
        if len(addr) != expected_len:
            addr_len, addr = addr[0], addr[1:]
            if addr_len != expected_len or len(addr) != expected_len:
                raise IndexToIpException(
                    "IPv%d address length is not %d: %r"
                    % (
                        4 if addr_type == IPV4_ID else 6,
                        expected_len,
                        oid,
                    )
                )

        return converter(addr)

    @classmethod
    def _chop_index(cls, index, entry):
        """
        Chops a prefix OID off an index OID, based on a table entry object.

        If the index is prefixed by the entry object itself, or by any of its
        descendants (columnar objects) in the MIB, that prefix is chopped off
        and the suffix is returned. Non-matches will return the index unchanged.

        :param index: An OID object or equivalent tuple
        :param entry: The name of an object in this MIB, preferable a table
                      entry object.
        :returns: An OID hobject.

        """
        index = OID(index)
        root = cls.nodes.get(entry, None)
        if not root or not root.oid.is_a_prefix_of(index):
            return index

        children = (c.oid for c in cls.nodes.values() if root.oid.is_a_prefix_of(c.oid))
        matched_prefixes = [c for c in children if c.is_a_prefix_of(index)] + [root.oid]
        if matched_prefixes:
            index = index.strip_prefix(matched_prefixes[0])

        return index

    @classmethod
    def address_index_to_ip(cls, index):
        """Convert a row index from ipAddressTable to an IP object."""

        index = cls._chop_index(index, 'ipAddressEntry')
        ip = cls.inetaddress_to_ip(index)
        return ip

    @classmethod
    def prefix_index_to_ip(cls, index, prefix_entry='ipAddressPrefixEntry'):
        """Convert a row index from ipAddressPrefixTable to an IP object."""

        index = cls._chop_index(index, prefix_entry)

        if len(index) < 4:
            cls._logger.debug("prefix_index_to_ip: index too short: %r", index)
            return None

        addr_oid = index[1:-1]
        prefix_length = index[-1]

        ip = cls.inetaddress_to_ip(addr_oid)
        if ip:
            prefix = ip.make_net(prefix_length)
            return prefix

    @inlineCallbacks
    def _get_ifindex_ip_mac_mappings(self, column='ipNetToPhysicalPhysAddress'):
        """Get IP/MAC mappings from a table indexed by IfIndex+InetAddressType+
        InetAddress.
        """
        all_phys_addrs = yield self.retrieve_column(column)

        mappings = set()

        for row_index, phys_address in all_phys_addrs.items():
            ifindex = row_index[0]
            inet_address = row_index[1:]
            ip = self.inetaddress_to_ip(inet_address)
            mac = self._binary_mac_to_hex(phys_address)

            row = (ifindex, ip, mac)
            mappings.add(row)
        self._logger.debug(
            "ip/mac pairs: Got %d rows from %s", len(all_phys_addrs), column
        )
        return mappings

    @inlineCallbacks
    def _get_ifindex_ipv4_mac_mappings(self, column='ipNetToMediaPhysAddress'):
        """Get IP/MAC mappings from a table indexed by IfIndex+IpAddress."""
        ipv4_phys_addrs = yield self.retrieve_column(column)

        mappings = set()
        ignore_count = 0

        for row_index, phys_address in ipv4_phys_addrs.items():
            ifindex = row_index[0]
            ip_address = row_index[1:]
            if len(ip_address) != 4:
                ignore_count += 1
                continue

            ip = oid_to_ipv4(ip_address)
            mac = self._binary_mac_to_hex(phys_address)

            row = (ifindex, ip, mac)
            mappings.add(row)

        if ignore_count:
            self._logger.warning(
                "ignored %d/%d invalid IPv4 addresses from %s",
                ignore_count,
                len(ipv4_phys_addrs),
                column,
            )
        self._logger.debug(
            "ip/mac pairs: Got %d rows from %s", len(ipv4_phys_addrs), column
        )
        return mappings

    @staticmethod
    def _binary_mac_to_hex(mac):
        "Converts a binary MAC address representation to a hexstring"
        return binary_mac_to_hex(mac)

    @inlineCallbacks
    def get_ifindex_ip_mac_mappings(self):
        """Retrieve the layer 3->layer 2 address mappings of this device.

        Will retrieve results from the new IP-version-agnostic table of IP-MIB,
        if there are no results it will retrieve from the deprecated IPv4-only
        table.

        Return value:
          A set of tuples: set([(ifindex, ip_address, mac_address), ...])
          ifindex will be an integer, ip_address will be an IPy.IP object and
          mac_address will be a string with a colon-separated hex representation
          of a MAC address.

        """
        mappings_new = yield self._get_ifindex_ip_mac_mappings()
        mappings_deprecated = yield self._get_ifindex_ipv4_mac_mappings()

        return mappings_new | mappings_deprecated

    @inlineCallbacks
    def _get_interface_ipv4_addresses(
        self, ifindex_column='ipAdEntIfIndex', netmask_column='ipAdEntNetMask'
    ):
        """Get IPv4 address information for interfaces from a table
        indexed by IpAddress.  Default is the ipAddrTable.

        """
        address_rows = yield self.retrieve_columns((ifindex_column, netmask_column))

        addresses = set()
        ignore_count = 0

        for row_index, row in address_rows.items():
            if len(row_index) != 4:
                ignore_count += 1
                continue

            ip = oid_to_ipv4(row_index)
            ifindex = row[ifindex_column]
            netmask = row[netmask_column]
            try:
                prefix = ip.make_net(netmask)
            except ValueError as err:
                self._logger.warning(
                    "ignoring IP address %s due to invalid netmask %s (%s)",
                    ip,
                    netmask,
                    err,
                )
            else:
                new_row = (ifindex, ip, prefix)
                addresses.add(new_row)

        if ignore_count:
            self._logger.warning(
                "ignored %d/%d invalid IPv4 addresses from %s",
                ignore_count,
                len(address_rows),
                ifindex_column,
            )
        self._logger.debug(
            "interface addresses: Got %d rows from %s",
            len(address_rows),
            ifindex_column,
        )
        return addresses

    @inlineCallbacks
    def _get_interface_addresses(
        self,
        ifindex_column='ipAddressIfIndex',
        prefix_column='ipAddressPrefix',
        prefix_entry='ipAddressPrefixEntry',
    ):
        """Get IP address information for interfaces from a table
        indexed by InetAddressType+InetAddress.  Default is the ipAddressTable.

        """
        address_rows = yield self.retrieve_columns((ifindex_column, prefix_column))

        addresses = set()
        unparseable_addrs = set()

        for row_index, row in address_rows.items():
            ip = self.inetaddress_to_ip(row_index)
            if not ip:
                unparseable_addrs.add(row_index)
                continue

            ifindex = row[ifindex_column]
            prefix_pointer = row[prefix_column]

            prefix = self.prefix_index_to_ip(prefix_pointer, prefix_entry)

            new_row = (ifindex, ip, prefix)
            addresses.add(new_row)

        if unparseable_addrs:
            self._logger.warning(
                "ignored %d invalid or unsupported addresses from %s: %r",
                len(unparseable_addrs),
                ifindex_column,
                unparseable_addrs,
            )
        self._logger.debug(
            "interface addresses: Got %d rows from %s",
            len(address_rows),
            ifindex_column,
        )
        return addresses

    @inlineCallbacks
    def get_interface_addresses(self):
        """Retrieve the IP addresses and prefixes of interfaces.

        Will retrieve results from the new IP-version-agnostic table of IP-MIB,
        then from the deprecated IPv4-only table.

        :returns: A set of tuples:
                  set([(ifindex, ip_address, prefix_address), ...])
                  ifindex will be an integer, ip_address and
                  prefix_address will be IPy.IP objects.

        """
        addrs_from_new_table = yield self._get_interface_addresses()
        addrs_from_deprecated_table = yield self._get_interface_ipv4_addresses()

        return addrs_from_new_table | addrs_from_deprecated_table

    @inlineCallbacks
    def get_ipv6_octet_counters(self):
        """For each applicable interface retrieves IPv6 octet in/out counters.

        :returns: A deferred with a dict {ifindex: (in_octets, out_octets)}

        """
        octets = yield self.retrieve_columns([IP_IN_OCTETS, IP_OUT_OCTETS])
        result = dict(
            (index[-1], (row[IP_IN_OCTETS], row[IP_OUT_OCTETS]))
            for index, row in octets.items()
            if index[-2] == IPV6_ID
        )
        return result


class MultiIpMib(IpMib, mibretriever.MultiMibMixIn):
    """A version of IpMib that supports collection of ip/mac mappings from multiple
    logical instances.
    """

    def get_ifindex_ip_mac_mappings(self):
        method = super().get_ifindex_ip_mac_mappings
        return self._multiquery(method, integrator=_set_integrator)


def _set_integrator(results):
    return set().union(*(result_set for vrf, result_set in results))


class IndexToIpException(Exception):
    """A collected OID row index could not be converted to an IP address"""

    pass
