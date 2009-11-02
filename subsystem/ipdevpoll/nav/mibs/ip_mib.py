# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 UNINETT AS
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
        addr_len = oid[1]
        addr = oid[2:]

        if addr_type == ipv4:
            if addr_len != 4 or len(addr) != 4:
                raise IndexToIpException("IPv4 address length is not 4: %r" %
                                         oid)
            addr_str = ".".join(str(i) for i in addr)

        elif addr_type == ipv6:
            if addr_len != 16 or len(addr) != 16:
                raise IndexToIpException("IPv6 address length is not 16: %r" %
                                         oid)
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

        if 'ipAddressEntry' in cls.nodes:
            entry = cls.nodes['ipAddressEntry']
            if entry.oid.isaprefix(index):
                # Chop off the entry OID+column prefix
                index = index[(len(entry.oid) + 1):]

        ip = cls.inetaddress_to_ip(index)
        return ip


    @classmethod
    def prefix_index_to_ip(cls, index):
        """Convert a row index from ipAddressPrefixTable to an IP object."""

        if 'ipAddressPrefixEntry' in cls.nodes:
            entry = cls.nodes['ipAddressPrefixEntry']
            if entry.oid.isaprefix(index):
                # Chop off the entry OID+column prefix
                index = index[(len(entry.oid) + 1):]

        if len(index) < 4:
            cls.logger.debug("prefix_index_to_ip: index too short: %r", index)
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
            ip = IpMib.inetaddress_to_ip(inet_address)
            mac = binary_mac_to_hex(phys_address)
            
            row = (ifindex, ip, mac)
            mappings.add(row)
        self.logger.debug("ip/mac pairs: Got %d rows from %s", 
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
        self.logger.debug("ip/mac pairs: Got %d rows from %s", 
                          len(ipv4_phys_addrs), column)
        yield mappings


    @defer.deferredGenerator
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
        waiter = defer.waitForDeferred(self._get_ifindex_ip_mac_mappings())
        yield waiter
        mappings = waiter.getResult()

        # Fall back to deprecated table if the IP-version agnostic
        # table gave no results.
        if len(mappings) == 0:
            waiter = defer.waitForDeferred(
                self._get_ifindex_ipv4_mac_mappings())
            yield waiter
            mappings = waiter.getResult()

        yield mappings


class IndexToIpException(Exception):
    pass
