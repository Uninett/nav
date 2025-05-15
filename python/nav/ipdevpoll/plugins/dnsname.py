#
# Copyright (C) 2008-2012, 2015 Uninett AS
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
"""
ipdevpoll plugin to perform reverse DNS lookups on netbox IP addresses.

Will generate events if there are mismatches between device sysname
and dnsname.
"""

from itertools import cycle

from IPy import IP

from twisted.internet import defer, error
from twisted.names import client, dns
from twisted.names.error import DomainError

from nav.ipdevpoll import Plugin, shadows

_resolvers = cycle([client.createResolver() for i in range(3)])


class DnsName(Plugin):
    """Performs reverse DNS lookup on netbox IP address"""

    @staticmethod
    def can_handle(netbox):
        "Handles anything, anytime, since we don't query the netbox directly"
        return True

    def handle(self):
        ip = IP(self.netbox.ip)
        self._logger.debug("Doing DNS PTR lookup for %s", ip.reverseName())
        # Use the OS configured DNS resolver method
        resolver = next(_resolvers)
        df = resolver.lookupPointer(ip.reverseName())
        df.addCallbacks(self._find_ptr_response, self._handle_failure, errbackArgs=ip)
        df.addCallback(self._log_name).addCallback(self._verify_name_change)
        return df

    def _handle_failure(self, failure, ip=None):
        """Logs DNS failures, but does not stop the job from running."""
        failtype = failure.trap(error.TimeoutError, defer.TimeoutError, DomainError)
        if failtype in (error.TimeoutError, defer.TimeoutError):
            self._logger.warning("DNS lookup timed out")
        elif failtype == DomainError:
            self._logger.warning(
                "DNS lookup error for %s: %s", ip, failure.type.__name__
            )

    def _find_ptr_response(self, dns_response):
        """
        Finds and returns a PTR record from a DNS response.

        If multiple records are found, prefer to keep the existing name,
        if still applicable.

        """
        self._logger.debug("DNS response: %s", dns_response)
        ptrs = (
            record
            for record_set in dns_response
            for record in record_set
            if record.type == dns.PTR
        )
        names = [str(record.payload.name) for record in ptrs]

        if len(names) > 1:
            self._logger.debug("found multiple PTR records: %s", names)
            if self.netbox.sysname in names:
                self._logger.debug("keeping old name for stability")
                return self.netbox.sysname

        if names:
            return names[0]

    def _log_name(self, dns_name):
        if not dns_name:
            self._logger.warning(
                "Unable to find PTR record for %s (%s)",
                self.netbox.ip,
                IP(self.netbox.ip).reverseName(),
            )
        else:
            self._logger.debug(
                "Reverse DNS lookup result: %s -> %s", self.netbox.ip, dns_name
            )
        return dns_name

    def _verify_name_change(self, new_name):
        if new_name:
            if new_name.strip().lower() != self.netbox.sysname.strip().lower():
                self._logger.warning(
                    "Box dnsname has changed from %s to %s",
                    repr(self.netbox.sysname),
                    repr(new_name),
                )
                netbox = self.containers.factory(None, shadows.Netbox)
                netbox.sysname = new_name

        return new_name
