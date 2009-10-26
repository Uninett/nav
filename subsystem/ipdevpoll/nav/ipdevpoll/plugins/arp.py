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

from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib
from nav.mibs.cisco_ietf_ip_mib import CiscoIetfIpMib
from nav.models import manage
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage, shadows
from nav.ipdevpoll.utils import binary_mac_to_hex, truncate_mac, find_prefix

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

        if shadows.Arp not in self.job_handler.containers:
            self.logger.warning("No ARP data found on %s." + \
                "All ARP records for this box will now time out." % self.netbox.sysname)
        self.timeout_arp(existing_arp)

        yield True

    def timeout_arp(self, result):
        """Sets end_time for all existing records that are not found in the new
        records.
        """
        # FIXME Should perhaps take new records as a parameter, instead of just
        # looking them up in self.job_handler.containers?
        for row in result:
            ip = IP(row.ip).strCompressed()
            key = (self.netbox, ip, row.mac)
            if shadows.Arp not in self.job_handler.containers or \
                    key not in self.job_handler.containers[shadows.Arp]:
                arp = self.job_handler.container_factory(shadows.Arp, key=row.id)
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
        def index_to_ip(index, type):
            if type == IP_MIB:
                ip_set = index[1:]
                return IpMib.index_to_ip(ip_set)
            elif type == IPV6_MIB:
                ip_set = index[1:]
                return Ipv6Mib.index_to_ip(ip_set)
            elif type == CISCO_MIB:
                if_index, ip_version, length = index[0:3]
                ip_set = index[3:]
                return CiscoIetfIpMib.index_to_ip(ip_version, ip_set)
            else:
                raise Exception("Unknown MIB type, %s,  specified." % type)

        for index, mac in result.items():
            try:
                ip = index_to_ip(index, type)
            except IndexToIpException, e:
                self.logger.warning(unicode(e))
                continue
            except Exception, e:
                self.logger.warning(unicode(e) + " Aborting ARP processing.")
                return

            ip_str = ip.strCompressed()
            mac = binary_mac_to_hex(mac)
            mac = truncate_mac(mac)

            arp = self.job_handler.container_factory(shadows.Arp, key=(
                self.netbox,
                ip_str,
                mac,
            ))
            arp.sysname = self.netbox.sysname
            arp.ip = ip_str
            arp.mac = mac
            arp.prefix = find_prefix(ip, prefix)
            arp.netbox = self.netbox
            arp.end_time = datetime.max
