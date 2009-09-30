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
"""ipdevpoll plugin to poll IP prefix information.

This plugin will use the IP-MIB, IPv6-MIB and CISCO-IETF-IP-MIB to
poll prefix information for both IPv4 and IPv6.

A revised version of the IP-MIB contains the IP-version-agnostic
ipAddressTable which is queried first, although not much equipment
supports this table yet.  It then falls back to the original IPv4-only
ipAddrTable, followed by the IPv6-MIB (which has been superseded by
the updated IP-MIB).  It also tries a Cisco proprietary
CISCO-IETF-IP-MIB, which is based on a draft that later became the
revised IP-MIB.

TODO: Figure out which VLAN each prefix belongs to.
TODO: Ignore single-host prefixes (32 bit IPv4 mask and 128 bit IPv6 mask)

"""

from twisted.internet import defer
from twisted.python.failure import Failure

from IPy import IP

from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib
from nav.mibs.cisco_ietf_ip_mib import CiscoIetfIpMib

from nav.ipdevpoll import Plugin, FatalPluginError
from nav.ipdevpoll import storage

class Prefix(Plugin):
    """
    ipdevpoll-plugin for collecting prefix information from monitored
    equipment.
    """
    def __init__(self, *args, **kwargs):
        Plugin.__init__(self, *args, **kwargs)
        self.deferred = defer.Deferred()

    @classmethod
    def can_handle(cls, netbox):
        """
        This plugin handles netboxes
        """
        return True

    @defer.deferredGenerator
    def handle(self):


        self.logger.debug("Collecting prefixes")
        netbox = self.job_handler.container_factory(storage.Netbox, key=None)

        ipmib = IpMib(self.job_handler.agent)
        ciscoip = CiscoIetfIpMib(self.job_handler.agent)

        # Traverse ipAddressTable and cIpAddressTable as more or less
        # identical tables, but skip the Cisco MIB if the first gives
        # results.
        for mib, ifindex_col, prefix_col in (
            (ipmib, 'ipAddressIfIndex', 'ipAddressPrefix'),
            (ciscoip, 'cIpAddressIfIndex', 'cIpAddressPrefix'),
            ):
            self.logger.debug("Trying address table from %s",
                              mib.mib['moduleName'])
            df = mib.retrieve_columns((ifindex_col, prefix_col))
            dw = defer.waitForDeferred(df)
            yield dw

            addresses = dw.getResult()

            for index, row in addresses.items():
                ip = ipmib.address_index_to_ip(index)
                if not ip:
                    continue

                prefix = ipmib.prefix_index_to_ip(row[prefix_col])
                ifindex = row[ifindex_col]

                self.create_containers(netbox, ifindex, prefix, ip)
            
            # If we got results, skip the remaining mibs
            if addresses:
                return

        self.logger.debug("Trying original ipAddrTable")
        df = ipmib.retrieve_columns(('ipAdEntIfIndex',
                                     'ipAdEntAddr',
                                     'ipAdEntNetMask'))
        dw = defer.waitForDeferred(df)
        yield dw

        result = dw.getResult()

        for row in result.values():
            ip = IP(row['ipAdEntAddr'])
            ifindex = row['ipAdEntIfIndex']
            net_prefix = ip.make_net(row['ipAdEntNetMask'])

            self.create_containers(netbox, ifindex, net_prefix, ip)


    def create_containers(self, netbox, ifindex, net_prefix, ip):
        """
        Utitilty method for creating the shadow-objects
        """
        interface = self.job_handler.container_factory(storage.Interface, key=ifindex)
        interface.ifindex = ifindex
        interface.netbox = netbox

        port_prefix = self.job_handler.container_factory(storage.GwPortPrefix, key=ip)
        port_prefix.interface = interface
        port_prefix.gw_ip = str(ip)

        if net_prefix:
            prefix = self.job_handler.container_factory(storage.Prefix, 
                                                        key=net_prefix)
            prefix.net_address = str(net_prefix)
            port_prefix.prefix = prefix


    def error(self, failure):
        """
        Return a failure to the ipdevpoll-deamon
        """
        if failure.check(defer.TimeoutError):
            # Transform TimeoutErrors to something else
            self.logger.error(failure.getErrorMessage())
            # Report this failure to the waiting plugin manager (RunHandler)
            exc = FatalPluginError("Cannot continue due to device timeouts")
            failure = Failure(exc)
        self.deferred.errback(failure)
