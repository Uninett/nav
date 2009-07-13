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
        ipmib = IpMib(self.job_handler.agent)
        df = ipmib.retrieve_columns(['ipAdEntIfIndex','ipAdEntAddr','ipAdEntNetMask'])
        dw = defer.waitForDeferred(df)
        yield dw

        netbox = self.job_handler.container_factory(storage.Netbox, key=None)

        results = dw.getResult()

        for result in results.values():
            ip = result['ipAdEntAddr']
            ifindex = result['ipAdEntIfIndex']
            net_prefix = str(IP(result['ipAdEntAddr']).make_net(result['ipAdEntNetMask']))

            interface = self.job_handler.container_factory(storage.Interface, key=ifindex)
            interface.ifindex = ifindex
            interface.netbox = netbox

            prefix = self.job_handler.container_factory(storage.Prefix, key=net_prefix)
            prefix.net_address = net_prefix

            port_prefix = self.job_handler.container_factory(storage.GwPortPrefix, key=ip)
            port_prefix.interface = interface
            port_prefix.prefix = prefix
            port_prefix.gw_ip = ip

        # Check IPv6 - Only Cisco for now, couldn't find any
        # netboxes that aswered on IPv6MIB correctly
        mib = CiscoIetfIpMib(self.job_handler.agent)
        df = mib.retrieve_table('cIpAddressTable')
        dw = defer.waitForDeferred(df)
        yield dw

        results = dw.getResult()

        for key, result in results.items():
            try:
                ip = Ipv6Mib.index_to_ip(key[2:])
                netmask = Ipv6Mib.index_to_ip(result['cIpAddressPrefix'][17:-1])
                pfx = result['cIpAddressPrefix'][-1]
                net_prefix = netmask.make_net(pfx)
                ifindex = result['cIpAddressIfIndex']

                interface = self.job_handler.container_factory(storage.Interface, key=ifindex)
                interface.ifindex = ifindex
                interface.netbox = netbox

                prefix = self.job_handler.container_factory(storage.Prefix, key=net_prefix)
                prefix.net_address = str(net_prefix)

                port_prefix = self.job_handler.container_factory(storage.GwPortPrefix, key=ip)
                port_prefix.interface = interface
                port_prefix.prefix = prefix
                port_prefix.gw_ip = str(ip)

            except IndexToIpException:
                pass

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
