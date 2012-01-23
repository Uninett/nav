# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
from IPy import IP

from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks, returnValue

from nav.oids import OID
from nav.ipdevpoll.utils import binary_mac_to_hex
import mibretriever

class IpMib(mibretriever.MibRetriever):
    from nav.smidumps.ip_mib import MIB as mib

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
        ipv4 = 1
        ipv6 = 2

        addr_type = oid[0]
        addr = oid[1:]

        if addr_type == ipv4:
            if len(addr) != 4:
                addr_len, addr = addr[0], addr[1:]
                if addr_len != 4 or len(addr) != 4:
                    raise IndexToIpException(
                        "IPv4 address length is not 4: %r" % (oid,))
            addr_str = ".".join(str(i) for i in addr)

        elif addr_type == ipv6:
            if len(addr) != 16:
                addr_len, addr = addr[0], addr[1:]
                if addr_len != 16 or len(addr) != 16:
                    raise IndexToIpException(
                        "IPv6 address length is not 16: %r" % (oid,))
            hex_groups = ["%02x%02x" % (addr[i], addr[i+1])
                          for i in range(0, len(addr), 2)]
            addr_str = ':'.join(hex_groups)

        else:
            # Unknown address type
            return

        return IP(addr_str)


    @classmethod
    def address_index_to_ip(cls, index):
        """Convert a row index from ipAddressTable to an IP object."""

        index = OID(index)
        if 'ipAddressEntry' in cls.nodes:
            entry = cls.nodes['ipAddressEntry']
            if entry.oid.is_a_prefix_of(index):
                # Chop off the entry OID+column prefix
                index = OID(index.strip_prefix(entry.oid)[1:])

        ip = cls.inetaddress_to_ip(index)
        return ip


    @classmethod
    def prefix_index_to_ip(cls, index,
                           prefix_entry='ipAddressPrefixEntry'):
        """Convert a row index from ipAddressPrefixTable to an IP object."""

        index = OID(index)
        if prefix_entry in cls.nodes:
            entry = cls.nodes[prefix_entry]
            if entry.oid.is_a_prefix_of(index):
                # Chop off the entry OID+column prefix
                index = OID(index.strip_prefix(entry.oid)[1:])

        if len(index) < 4:
            cls._logger.debug("prefix_index_to_ip: index too short: %r", index)
            return None

        ifindex = index[0]
        addr_oid = index[1:-1]
        prefix_length = index[-1]

        ip = cls.inetaddress_to_ip(addr_oid)
        if ip:
            prefix = ip.make_net(prefix_length)
            return prefix

    @defer.deferredGenerator
    def _get_ifindex_ip_mac_mappings(self, 
                                     column='ipNetToPhysicalPhysAddress'):
        """Get IP/MAC mappings from a table indexed by IfIndex+InetAddressType+
        InetAddress.
        """
        waiter = defer.waitForDeferred(self.retrieve_column(column))
        yield waiter
        all_phys_addrs = waiter.getResult()

        mappings = set()

        for row_index, phys_address in all_phys_addrs.items():
            ifindex = row_index[0]
            inet_address = row_index[1:]
            ip = self.inetaddress_to_ip(inet_address)
            mac = binary_mac_to_hex(phys_address)
            
            row = (ifindex, ip, mac)
            mappings.add(row)
        self._logger.debug("ip/mac pairs: Got %d rows from %s",
                           len(all_phys_addrs), column)
        yield mappings

    @defer.deferredGenerator
    def _get_ifindex_ipv4_mac_mappings(self, column='ipNetToMediaPhysAddress'):
        """Get IP/MAC mappings from a table indexed by IfIndex+IpAddress."""
        waiter = defer.waitForDeferred(self.retrieve_column(column))
        yield waiter
        ipv4_phys_addrs = waiter.getResult()

        mappings = set()

        for row_index, phys_address in ipv4_phys_addrs.items():
            ifindex = row_index[0]
            ip_address = row_index[1:]
            ip_address_string = ".".join([str(i) for i in ip_address])
            ip = IP(ip_address_string)
            mac = binary_mac_to_hex(phys_address)

            row = (ifindex, ip, mac)
            mappings.add(row)
        self._logger.debug("ip/mac pairs: Got %d rows from %s",
                           len(ipv4_phys_addrs), column)
        yield mappings


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

        returnValue(mappings_new | mappings_deprecated)


    @defer.deferredGenerator
    def _get_interface_ipv4_addresses(self, 
                                      ifindex_column='ipAdEntIfIndex',
                                      netmask_column='ipAdEntNetMask'):
        """Get IPv4 address information for interfaces from a table
        indexed by IpAddress.  Default is the ipAddrTable.

        """
        waiter = defer.waitForDeferred(
            self.retrieve_columns((ifindex_column, netmask_column)))
        yield waiter
        address_rows = waiter.getResult()

        addresses = set()

        for row_index, row in address_rows.items():
            ip_address_string = ".".join([str(i) for i in row_index])
            ip = IP(ip_address_string)
            ifindex = row[ifindex_column]
            netmask = row[netmask_column]
            prefix = ip.make_net(netmask)

            new_row = (ifindex, ip, prefix)
            addresses.add(new_row)
        self._logger.debug("interface addresses: Got %d rows from %s",
                           len(address_rows), ifindex_column)
        yield addresses

    @defer.deferredGenerator
    def _get_interface_addresses(self, 
                                 ifindex_column='ipAddressIfIndex',
                                 prefix_column='ipAddressPrefix',
                                 prefix_entry='ipAddressPrefixEntry'):
        """Get IP address information for interfaces from a table
        indexed by InetAddressType+InetAddress.  Default is the ipAddressTable.

        """
        waiter = defer.waitForDeferred(
            self.retrieve_columns((ifindex_column, prefix_column)))
        yield waiter
        address_rows = waiter.getResult()

        addresses = set()

        for row_index, row in address_rows.items():
            ip = self.inetaddress_to_ip(row_index)
            ifindex = row[ifindex_column]
            prefix_pointer = row[prefix_column]

            prefix = self.prefix_index_to_ip(prefix_pointer, prefix_entry)

            new_row = (ifindex, ip, prefix)
            addresses.add(new_row)
        self._logger.debug("interface addresses: Got %d rows from %s",
                           len(address_rows), ifindex_column)
        yield addresses

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

        returnValue(addrs_from_new_table | addrs_from_deprecated_table)


class IndexToIpException(Exception):
    pass
