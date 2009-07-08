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

from nav.mibs import IpMib, Ipv6Mib, CiscoIetfIpMib
from nav.models import manage
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage

IP_MIB = 1
IPV6_MIB = 2
CISCO_MIB = 3

class Arp(Plugin):
    @classmethod
    def can_handle(cls, netbox):
        if netbox.category.id == 'GW' or \
                netbox.category.id == 'GSW':
            return True
        else:
            return False

    @defer.deferredGenerator
    def handle(self):
        self.logger.debug("Collecting ARP")
        try_vendor = False

        # Fetch standard MIBs
        ip_mib = IpMib(self.job_handler.agent)
        df = defer.waitForDeferred(
            ip_mib.retrieve_column('ipNetToMediaPhysAddress'))
        yield df
        ip_result = df.getResult()

        ipv6_mib = Ipv6Mib(self.job_handler.agent)
        df = defer.waitForDeferred(
            ipv6_mib.retrieve_column('ipv6NetToMediaPhysAddress'))
        yield df
        ip6_result = df.getResult()

        if len(ip_result) > 0:
            self.logger.debug("Found %d ARP entries" % len(ip_result))
            self.process_arp(ip_result, type=IP_MIB)
        else:
            try_vendor = True

        if len(ip6_result) > 0:
            self.logger.debug("Found %d NDP entries" % len(ip6_result))
            self.process_arp(ip6_result, type=IPV6_MIB)
        else:
            try_vendor = True

        if try_vendor:
            # Try Cisco specific MIBs
            cisco_mib = CiscoIetfIpMib(self.job_handler.agent)
            thing = defer.waitForDeferred(
                cisco_mib.retrieve_column('cInetNetToMediaPhysAddress'))
            yield thing
            result = thing.getResult()
            self.logger.debug("Found %d Cisco ARP entries" % len(result))
            self.process_arp(result, type=CISCO_MIB)

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
        for row in result:
            ip = IP(row.ip).strNormal()
            key = (self.netbox, ip, row.mac)
            if storage.Arp not in self.job_handler.containers or \
                    key not in self.job_handler.containers[storage.Arp]:
                arp = self.job_handler.container_factory(storage.Arp, key=key)
                arp.ip = ip
                arp.mac = row.mac
                arp.netbox = self.netbox
                arp.sysname = self.netbox.sysname
                arp.start_time = row.start_time
                arp.end_time = datetime.utcnow()
                self.logger.debug('Timeout on %s for %s' % (row.mac, ip))

    def process_arp(self, result, type=IP_MIB):
        if type == IP_MIB:
            index_to_ip = ipmib_index_to_ip
        elif type == IPV6_MIB:
            index_to_ip = ipv6mib_index_to_ip
        elif type == CISCO_MIB:
            index_to_ip = ciscomib_index_to_ip
            return
        else:
            raise Exception('Unknown IP type specified')

        for index, mac in result.items():
            ip = index_to_ip(index)
            ip = ip.strNormal()
            mac = binary_mac_to_hex(mac)
            mac = truncate_mac(mac)
#            print "row %d %s %s" % (type, ip, mac)

            arp = self.job_handler.container_factory(storage.Arp, key=(
                self.netbox,
                unicode(ip),
                mac,
            ))
            #arp.prefix = Something
            arp.sysname = self.netbox.sysname
            arp.ip = ip
            arp.mac = mac
            arp.netbox = self.netbox
            arp.start_time = datetime.utcnow()
            arp.end_time = datetime.max

def binary_mac_to_hex(binary_mac):
    """Convert a binary string MAC address to hex string."""
    if binary_mac:
        return ":".join("%02x" % ord(x) for x in binary_mac)

def truncate_mac(mac):
    parts = mac.split(':')
    if len(parts) > 6:
        mac = ':'.join(parts[:6])
    return mac

def ipmib_index_to_ip(index):
    offset = len(index) - 4
    if offset < 0:
        raise Exception()

    ip_set = index[offset:]
    ip = '.'.join(["%d" % part for part in ip_set])
    return IP(ip)

def ipv6mib_index_to_ip(index):
    offset = len(index) - 16
    if offset < 0:
        raise Exception()

    ip_set = index[offset:]
    ip_hex = ["%02x" % part for part in ip_set]
    ip = ':'.join([ip_hex[n] + ip_hex[n+1] for n,v in enumerate(ip_hex) if n % 2 == 0])
    return IP(ip)

def ciscomib_index_to_ip(index):
    ifIndex, ip_ver, length = index[0:3]
    if ip_ver == 1:
        return ipmib_index_to_ip(index[3:])
    elif ip_ver == 2:
        return ipv6mib_index_to_ip(index[3:])
