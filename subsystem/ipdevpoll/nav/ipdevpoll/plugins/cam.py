# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
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
"""Dynamic CAM record collecting with and without community string indexing.
"""

from datetime import datetime

from twisted.internet import defer, threads
from twisted.python.failure import Failure
from twistedsnmp import snmpprotocol, agentproxy

from nav.mibs.if_mib import IfMib
from nav.mibs.bridge_mib import BridgeMib
from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage
from nav.ipdevpoll.utils import binary_mac_to_hex
from nav.models import manage
from nav.util import round_robin

MAX_MISS_COUNT = 3

class Cam(Plugin):
    """Collects dynamic CAM records"""

    def __init__(self, *args, **kwargs):
        super(Cam, self).__init__(*args, **kwargs)
        self.cam = {}
        self.existing_cam = {}
        self.result = {}

    @classmethod
    def can_handle(cls, netbox):
        return True

    @defer.deferredGenerator
    def handle(self):
        self.logger.debug("Collecting CAM logs")

        bridge_mib = BridgeMib(self.job_handler.agent)
        if_mib = IfMib(self.job_handler.agent)

        # If cs_at_vlan is False we can skip community string indexing.
        # If it's None we try community string indexing, since we can't really
        # know for sure if it's supported or not.
        if self.netbox.type.cs_at_vlan == False:
            vlans = []
        else:
            dw = defer.waitForDeferred(
                self._get_vlans())
            yield dw
            vlans = dw.getResult()

        if len(vlans) > 0:
            # Try polling mac/port data with community string indexing
            agents = CommunityIndexAgentProxy(self.netbox)
            for vlan in vlans:
                agent = agents.agent_for_vlan(vlan)
                vlan_bridge_mib = BridgeMib(agent)
                dw = defer.waitForDeferred(self._fetch_macs(vlan_bridge_mib))
                yield dw

                try:
                    num = dw.getResult()
                except defer.TimeoutError:
                    self.logger.debug("Timeout on vlan %d" % vlan)
                else:
                    self.logger.debug("Found %d macs on vlan %d" % (num, vlan))

        if len(self.result) == 0 or len(vlans) == 0:
            # No result or no vlans, poll mac/port data without community
            # string indexing
            self.logger.debug("Trying to fetch cam without community index")
            dw = defer.waitForDeferred(self._fetch_macs(bridge_mib))
            yield dw
            num = dw.getResult()
            self.logger.debug("Found %d macs for netbox" % num)

        # Fetch interface to port descriptions
        dw = defer.waitForDeferred(
            if_mib.retrieve_column('ifName'))
        yield dw
        ifname_result = dw.getResult()
        self._process_cam(ifname_result)

        # Get all existing cam records
        dw = defer.waitForDeferred(threads.deferToThread(
            self._fetch_cam))
        yield dw
        self.existing_cam = dw.getResult()

        self._store()
        self._timeout_cam()

        yield True

    def _store(self):
        """Store found cam data.

        If we find a record that already exist in the database, but has a miss
        count, we reset the miss count and end time.
        """
        for key, row in self.cam.items():
            cam = self.job_handler.container_factory(storage.Cam, key=key)
            if key in self.existing_cam:
                cam.id = self.existing_cam[key].id
                if self.existing_cam[key].miss_count > 0:
                    self.logger.debug(
                        "Resetting miss count and end time on ifindex %s/mac %s" % (
                            self.existing_cam[key].ifindex,
                            self.existing_cam[key].mac,
                    ))
            else:
                cam.start_time = datetime.now()

            cam.netbox = self.netbox
            cam.sysname = self.netbox.sysname
            cam.ifindex = row['ifindex']
            # cam.module
            cam.port = row['port']
            cam.mac = row['mac']
            cam.end_time = datetime.max
            cam.miss_count = 0

    def _timeout_cam(self):
        """Compares existing cam records in the database to what was found
        during this polling run.

        Records that are no longer found will get their miss count increased
        untill they reach the maximum miss count. They are then considered
        closed.
        """
        for key, row in self.existing_cam.items():
            if key not in self.cam:
                cam = self.job_handler.container_factory(storage.Cam, key=key)
                cam.id = row.id
                if row.miss_count == 0:
                    cam.miss_count = 1
                    cam.end_time = datetime.now()
                    self.logger.debug(
                        "ifindex %s/mac %s is no longer found, miss count 1" % (
                        row.ifindex, row.mac
                    ))
                elif row.miss_count >= MAX_MISS_COUNT:
                    cam.miss_count = None
                    message = "ifindex %s/mac %s reached maximum miss count" % (
                        row.ifindex, row.mac
                    )
                    message += " and is considered gone."
                    self.logger.debug(message)
                else:
                    cam.miss_count = row.miss_count + 1
                    self.logger.debug(
                        "ifindex %s/mac %s miss count is %d" % (
                        row.ifindex, row.mac, cam.miss_count
                    ))

    @defer.deferredGenerator
    def _fetch_macs(self, bridge_mib):
        """Polls cam data.

        Uses the given bridge_mib.

        Sets self.result to a dictionary indexed by ifindex. Values are a list
        of macs.

        Returns number of found macs.
        """

        def process_mac_result(mac_result):
            result = {}
            for index, row in mac_result.items():
                mac = binary_mac_to_hex(row['dot1dTpFdbAddress'])
                port = row['dot1dTpFdbPort']
                if port not in result:
                    result[port] = []
                result[port].append(mac)
            return result

        df = bridge_mib.retrieve_columns([
                'dot1dTpFdbAddress',
                'dot1dTpFdbPort',
            ])
        dw = defer.waitForDeferred(df)
        yield dw
        result = dw.getResult()
        mac_result = process_mac_result(dw.getResult())
        num = len(result)

        df = bridge_mib.retrieve_column('dot1dBasePortIfIndex')
        dw = defer.waitForDeferred(df)
        yield dw
        result = dw.getResult()

        for (port,), ifindex in result.items():
            if ifindex not in self.result:
                self.result[ifindex] = []
            self.result[ifindex] = mac_result.get(port, [])

        yield num

    def _process_cam(self, ifname_result):
        """Combines self.result with ifname_result.
        Sets self.cam to a dictionary where the keys are netbox id, ifindex and
        mac.
        """
        for (ifindex,), portname in ifname_result.items():
            if ifindex in self.result:
                macs = self.result[ifindex]
                for mac in macs:
                    key = (self.netbox.id, ifindex, mac)
                    self.cam[key] = {
                        'ifindex': ifindex,
                        'module': None,
                        'port': portname,
                        'mac': mac,
                    }

    def _get_vlans(self):
        """Fetches all vlans from the database.
        """
        queryset = manage.Interface.objects.filter(
                netbox__id=self.netbox.id
            )
        interfaces = storage.shadowify_queryset(queryset)

        vlans = []
        for interface in interfaces:
            if interface.vlan and interface.vlan not in vlans:
                vlans.append(interface.vlan)

        return defer.succeed(vlans)

    def _fetch_cam(self):
        """Fetches all cam data from the database.
        Returns a dictionary where the keys are tuples of netbox id, if index
        and mac.
        """
        queryset = manage.Cam.objects.filter(
                netbox__id=self.netbox.id,
                miss_count__isnull=False,
            )
        shadow = storage.shadowify_queryset(queryset)

        result = {}
        for row in shadow:
            key = (row.netbox.id, row.ifindex, row.mac)
            result[key] = row
        return result

class CommunityIndexAgentProxy(object):
    """Makes agent proxies with community string indexing"""

    def __init__(self, netbox):
        self.netbox = netbox
        self.ports = round_robin([snmpprotocol.port() for i in range(10)])

    def agent_for_vlan(self, vlan):
        """Returns a new agent proxy with community string index set to the
        given vlan.
        """
        community = "%s@%s" % (self.netbox.read_only, vlan)
        port = self.ports.next()
        agent = agentproxy.AgentProxy(
            self.netbox.ip, 161,
            community=community,
            snmpVersion='v%s' % self.netbox.snmp_version,
            protocol=port.protocol,
        )
        return agent
