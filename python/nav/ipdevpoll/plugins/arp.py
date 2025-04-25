# -*- coding: utf-8 -*-
#
# Copyright (C) 2009-2012 Uninett AS
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
"""ipdevpoll plugin to log IP / MAC address pairings from routers.

There are basically four methods to collect this via SNMP, some of
which are deprecated, but still in use by vendors.  This plugin will
support all four methods.

IP-MIB contains two tables:
  ipNetToMediaTable     -- deprecated, as it contains only entries for IPv4.
  ipNetToPhysicalTable  -- current, address version agnostic table

IPV6-MIB has been abandoned in favor of the revised IP-MIB, but has one table:
  ipv6NetToMediaTable

CISCO-IETF-IP-MIB       -- based on an early draft of the revised IP-MIB
  cInetNetToMediaTable

Although the ARP protocol is only related to IPv4, this plugin keeps
the name for historical reasons.

"""

import operator
from datetime import datetime, timedelta

from IPy import IP
from twisted.internet import defer

from nav.enterprise.ids import VENDOR_ID_ARISTA_NETWORKS_INC_FORMERLY_ARASTRA_INC
from nav.ipdevpoll.utils import get_arista_vrf_instances
from nav.mibs.ip_mib import IpMib, MultiIpMib
from nav.mibs.ipv6_mib import Ipv6Mib
from nav.mibs.cisco_ietf_ip_mib import CiscoIetfIpMib

from nav.models import manage
from nav.ipdevpoll import Plugin, db
from nav.ipdevpoll import storage, shadows

INCOMPLETE_MAC = '00:00:00:00:00:00'


class Arp(Plugin):
    """Collects ARP records for IPv4 devices and NDP cache for IPv6 devices."""

    prefix_cache = []  # prefix cache, should be sorted by descending mask length
    prefix_cache_update_time = datetime.min
    prefix_cache_max_age = timedelta(minutes=5)

    @classmethod
    def can_handle(cls, netbox):
        """This will only be useful on layer 3 devices, i.e. GW/GSW devices."""
        daddy_says_ok = super(Arp, cls).can_handle(netbox)
        return daddy_says_ok and netbox.category.id in ('GW', 'GSW')

    @defer.inlineCallbacks
    def handle(self):
        yield self._check_and_update_prefix_cache()
        if self._is_arp_already_collected():
            self._logger.debug("ARP records already collected for this device")
            return
        self._logger.debug("Collecting IP/MAC mappings")

        # Fetch standard MIBs
        ip_mib = yield self._get_ip_mib()
        mappings = yield ip_mib.get_ifindex_ip_mac_mappings()
        self._logger.debug("Found %d mappings in IP-MIB", len(mappings))

        # Try IPV6-MIB if no IPv6 results were found in IP-MIB
        if not ipv6_address_in_mappings(mappings):
            ipv6_mib = Ipv6Mib(self.agent)
            ipv6_mappings = yield ipv6_mib.get_ifindex_ip_mac_mappings()
            self._logger.debug("Found %d mappings in IPV6-MIB", len(ipv6_mappings))
            mappings.update(ipv6_mappings)

        # If we got no results, or no IPv6 results, try vendor specific MIBs
        if not mappings or not ipv6_address_in_mappings(mappings):
            cisco_ip_mib = CiscoIetfIpMib(self.agent)
            cisco_ip_mappings = yield cisco_ip_mib.get_ifindex_ip_mac_mappings()
            self._logger.debug(
                "Found %d mappings in CISCO-IETF-IP-MIB", len(cisco_ip_mappings)
            )
            mappings.update(cisco_ip_mappings)

        yield self._process_data(mappings)

    @classmethod
    @defer.inlineCallbacks
    def _check_and_update_prefix_cache(cls):
        """Updates the prefix cache if deemed necessary"""
        prefix_cache_age = datetime.now() - cls.prefix_cache_update_time
        if prefix_cache_age > cls.prefix_cache_max_age:
            yield cls._update_prefix_cache()

    def _is_arp_already_collected(self):
        """Returns True if ARP entries have already been collected in this run"""
        return shadows.Arp in self.containers and bool(self.containers[shadows.Arp])

    @defer.inlineCallbacks
    def _get_ip_mib(self):
        if not self.is_arista():
            return IpMib(self.agent)  # regular IpMib for regular folks
        else:
            instances = yield get_arista_vrf_instances(self.agent)
            return MultiIpMib(self.agent, instances=instances)

    def is_arista(self):
        """Returns True if this is an Arista device"""
        return (
            self.netbox.type
            and self.netbox.type.get_enterprise_id()
            == VENDOR_ID_ARISTA_NETWORKS_INC_FORMERLY_ARASTRA_INC
        )

    @defer.inlineCallbacks
    def _process_data(self, mappings):
        """Process collected mapping data.

        1. Find all open ARP database records for this netbox
        2. Add Arp containers for all newly discovered mappings
        3. Add Arp containers to expire missing mappings

        """
        # Collected mappings include ifindexes.  Arp table doesn't
        # care about this, so we prune those.
        found_mappings = set(
            (ip, mac) for (ifindex, ip, mac) in mappings if mac != INCOMPLETE_MAC
        )
        stripped = len(mappings) - len(found_mappings)
        if stripped:
            self._logger.debug("stripped %d incomplete mappings", stripped)

        # Get open mappings from database to compare with
        open_mappings = yield self._load_existing_mappings()

        new_mappings = found_mappings.difference(open_mappings)
        expireable_mappings = set(open_mappings).difference(found_mappings)

        self._logger.debug(
            "Mappings: %d new / %d expired / %d kept",
            len(new_mappings),
            len(expireable_mappings),
            len(open_mappings) - len(expireable_mappings),
        )

        self._make_new_mappings(new_mappings)
        self._expire_arp_records(
            open_mappings[mapping] for mapping in expireable_mappings
        )

    @defer.inlineCallbacks
    def _load_existing_mappings(self):
        """Load the existing ARP records for this box from the db.

        Returns:

          A deferred whose result is a dictionary: { (ip, mac): arpid }
        """
        self._logger.debug("Loading open arp records from database")
        open_arp_records_queryset = manage.Arp.objects.filter(
            netbox__id=self.netbox.id, end_time__gte=datetime.max
        ).values('id', 'ip', 'mac')
        open_arp_records = yield db.run_in_thread(
            storage.shadowify_queryset_and_commit, open_arp_records_queryset
        )
        self._logger.debug("Loaded %d open records from arp", len(open_arp_records))

        open_mappings = dict(
            ((IP(arp['ip']), arp['mac']), arp['id']) for arp in open_arp_records
        )
        return open_mappings

    @classmethod
    def _update_prefix_cache(cls):
        cls.prefix_cache_update_time = datetime.now()
        df = db.run_in_thread(cls._load_prefixes_synchronously)
        df.addCallback(cls._update_prefix_cache_with_result)
        return df

    @classmethod
    def _load_prefixes_synchronously(cls):
        return list(manage.Prefix.objects.all().values('id', 'net_address'))

    @classmethod
    def _update_prefix_cache_with_result(cls, prefixes):
        cls._logger.debug("Populating prefix cache with %d prefixes", len(prefixes))

        prefixes = [(IP(p['net_address']), p['id']) for p in prefixes]
        prefixes.sort(key=operator.itemgetter(1), reverse=True)

        del cls.prefix_cache[:]
        cls.prefix_cache.extend(prefixes)

    def _make_new_mappings(self, mappings):
        """Convert a sequence of (ip, mac) tuples into a Arp shadow containers.

        Arguments:

          mappings -- An iterable containing tuples: (ip, mac)

        """
        netbox = self.containers.factory(None, shadows.Netbox)
        timestamp = datetime.now()
        infinity = datetime.max

        for ip, mac in mappings:
            if not ip or not mac:
                continue  # Some devices seem to return empty results!
            arp = self.containers.factory((ip, mac), shadows.Arp)
            arp.netbox = netbox
            arp.sysname = self.netbox.sysname
            arp.ip = ip.strCompressed()
            arp.mac = mac
            arp.prefix_id = self._find_largest_matching_prefix(ip)
            arp.start_time = timestamp
            arp.end_time = infinity

    def _expire_arp_records(self, arp_ids):
        """Create containers to force expiry of a set of Arp records.

        Arguments:

          arp_ids -- An iterable containing db primary keys for Arp records.

        """
        timestamp = datetime.now()

        for arp_id in arp_ids:
            arp = self.containers.factory(arp_id, shadows.Arp)
            arp.id = arp_id
            arp.end_time = timestamp

    def _find_largest_matching_prefix(self, ip):
        """Find the largest prefix that ip is part of.

        Returns:

          An integer prefix ID, or None if no matches were found.
        """
        for prefix_addr, prefix_id in self.prefix_cache:
            if ip in prefix_addr:
                return prefix_id


def ipv6_address_in_mappings(mappings):
    """Return True if there are any IPv6 addresses in mappings.

    Mappings must be an iterable of tuples: (foo, ip, bar).

    """
    for _, ip, _ in mappings:
        if ip and ip.version() == 6:
            return True
    return False
