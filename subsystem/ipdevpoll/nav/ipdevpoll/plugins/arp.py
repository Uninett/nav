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

import logging
from IPy import IP
from datetime import datetime

from twisted.internet import defer, threads
from twisted.python.failure import Failure
from django.db import connection

from nav.mibs import IpMib, Ipv6Mib, CiscoIetfIpMib
from nav.models import manage
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage

# MIB objects used
IP_MIB = 'ipNetToMediaPhysAddress'
IPV6_MIB = 'ipv6NetToMediaPhysAddress'
CISCO_MIB = 'cInetNetToMediaPhysAddress'

class Arp(Plugin):
    """Collects ARP records for IPv4 devices and NDP cache for IPv6 devices."""

    @classmethod
    def can_handle(cls, netbox):
        """ARP and NDP are for level 2 devices.
        Return true for netboxes with category GW or GSW.
        """
        if netbox.category.id in ('GW', 'GSW'):
            return True
        else:
            return False

    @defer.deferredGenerator
    def handle(self):
        self.logger.debug("Collecting ARP")
        try_vendor = False

        # Fetch prefixes
        thing = defer.waitForDeferred(threads.deferToThread(
            storage.shadowify_queryset, manage.Prefix.objects.all()))
        yield thing
        prefix = thing.getResult()

        # Fetch standard MIBs
        ip_mib = IpMib(self.job_handler.agent)
        df = defer.waitForDeferred(ip_mib.retrieve_column(IP_MIB))
        yield df
        ip_result = df.getResult()

        ipv6_mib = Ipv6Mib(self.job_handler.agent)
        df = defer.waitForDeferred(ipv6_mib.retrieve_column(IPV6_MIB))
        yield df
        ip6_result = df.getResult()

        # Process results from the standard MIB set
        if len(ip_result) > 0:
            self.logger.debug("Found %d ARP entries" % len(ip_result))
            self.process_arp(ip_result, type=IP_MIB, prefix=prefix)
        else:
            try_vendor = True

        if len(ip6_result) > 0:
            self.logger.debug("Found %d NDP entries" % len(ip6_result))
            self.process_arp(ip6_result, type=IPV6_MIB, prefix=prefix)
        else:
            try_vendor = True

        # Try vendor specific MIBs if either of the standard MIBs didn't get
        # any results.
        if try_vendor:
            # Try Cisco specific MIBs
            cisco_mib = CiscoIetfIpMib(self.job_handler.agent)
            thing = defer.waitForDeferred(cisco_mib.retrieve_column(CISCO_MIB))
            yield thing
            result = thing.getResult()
            self.logger.debug("Found %d Cisco ARP entries" % len(result))
            self.process_arp(result, type=CISCO_MIB, prefix=prefix)

        # Timeout records that we can't find any more
        existing_arp = manage.Arp.objects.filter(
            netbox__id=self.netbox.id,
            end_time=datetime.max,
        )
        thing = defer.waitForDeferred(
            threads.deferToThread(storage.shadowify_queryset, existing_arp))
        yield thing
        result = thing.getResult()

        if storage.Arp not in self.job_handler.containers:
            self.logger.warning("No ARP data found on %s." + \
                "All ARP records for this box will now time out." % self.netbox.sysname)
        self.timeout_arp(existing_arp)

        yield True

    def timeout_arp(self, result):
        """Sets end_time for all existing records that are not found in the new
        records.
        """
        for row in result:
            ip = IP(row.ip).strCompressed()
            key = (self.netbox, ip, row.mac)
            if storage.Arp not in self.job_handler.containers or \
                    key not in self.job_handler.containers[storage.Arp]:
                arp = self.job_handler.container_factory(storage.Arp, key=row.id)
                arp.id = row.id
                arp.end_time = datetime.utcnow()
                self.logger.debug('Timeout on %s for %s' % (row.mac, ip))


    def process_arp(self, result, type=IP_MIB, prefix=[]):
        """Takes a MibRetriever result row and processes it into Arp shadow
        objects.

        Parameters:
            result - The result from MibRetriever
            type   - The MIB OID name used. Used to format IP addresses.
            prefix - Prefix objects fetched from the database.
        """
        def find_prefix(ip, prefix):
            ret = None
            for p in prefix:
                sub = IP(p.net_address)
                if ip in sub:
                    # Return the most precise prefix, ie the longest prefix
                    if not ret or IP(ret.net_address).prefixlen() < sub.prefixlen():
                        ret = p
            return ret

        def index_to_ip(index, type):
            if type == IP_MIB:
                return ipmib_index_to_ip(index)
            elif type == IPV6_MIB:
                return ipv6mib_index_to_ip(index)
            elif type == CISCO_MIB:
                return ciscomib_index_to_ip(index)
            else:
                raise Exception("Unknown MIB type, %s,  specified." % type)

        for index, mac in result.items():
            try:
                ip = index_to_ip(index, type)
            except Exception, e:
                self.logger.debug(e, "Aborting ARP processing.")
                return

            ip_str = ip.strCompressed()
            mac = binary_mac_to_hex(mac)
            mac = truncate_mac(mac)

            arp = self.job_handler.container_factory(storage.Arp, key=(
                self.netbox,
                ip_str,
                mac,
            ))
            arp.sysname = self.netbox.sysname
            arp.ip = ip_str
            arp.mac = mac
            arp.prefix = find_prefix(ip, prefix)
            arp.netbox = self.netbox
            arp.start_time = datetime.utcnow()
            arp.end_time = datetime.max

def binary_mac_to_hex(binary_mac):
    """Convert a binary string MAC address to hex string."""
    if binary_mac:
        return ":".join("%02x" % ord(x) for x in binary_mac)

def truncate_mac(mac):
    """Takes a MAC address on the form xx:xx:xx... of any length and returns
    the first 6 parts.
    """
    parts = mac.split(':')
    if len(parts) > 6:
        mac = ':'.join(parts[:6])
    return mac

def ipmib_index_to_ip(index):
    """The index of ipNetToMediaPhysAddress is 5 parts (5 bytes in raw SNMP,
    represented as a 5-tuple in python).

    The first part is an ifIndex, the remaining 4 parts is the IPv4 address for
    the MAC address returned.

    This function joins those four parts and returns an IP object.
    """
    # Use the last 4 parts
    offset = len(index) - 4
    if offset < 0:
        raise Exception()

    ip_set = index[offset:]
    ip = '.'.join(["%d" % part for part in ip_set])
    return IP(ip)

def ipv6mib_index_to_ip(index):
    """The index of ipv6NetToMediaPhysAddress is 17 parts (17 bytes in raw SNMP
    represented as a 17-tuple in python).

    The first part is an ifIndex, the remaining 16 is the IPv6 address for the
    MAC address returned.

    This function joins those 16 parts and returns an IP object.
    """
    # Use the last 16 parts
    offset = len(index) - 16
    if offset < 0:
        raise Exception()

    ip_set = index[offset:]
    ip_hex = ["%02x" % part for part in ip_set]
    ip = ':'.join([ip_hex[n] + ip_hex[n+1] for n,v in enumerate(ip_hex) if n % 2 == 0])
    return IP(ip)

def ciscomib_index_to_ip(index):
    """The index of cInetNetToMediaPhysAddress is of undetermined length, but
    the first 3 parts are always ifIndex, ip version and length.

    The remaining parts should either be of length 4 or 16, depending of ip
    version.

    This function checks the ip version and calls ipmib_index_to_ip if it's a
    IPv4 address or ipv6mib_index_to_ip if it's a IPv6 address.
    """
    ifIndex, ip_ver, length = index[0:3]
    ip = index[3:]
    if ip_ver == 1:
        return ipmib_index_to_ip(ip)
    elif ip_ver == 2:
        return ipv6mib_index_to_ip(ip)
    elif ip_ver == 3:
        # FIXME IP with zone, what to do?
        return ipmib_index_to_ip(ip[:-1])
    elif ip_ver = 4:
        # FIXME IPv6 with zone, what to do?
        return ipv6mib_index_to_ip(ip[:-1])
    else:
        raise Exception('Unknown ip version from Cisco MIB.')
