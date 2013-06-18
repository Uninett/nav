#
# Copyright (C) 2003,2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""DNS service checker"""

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
from nav.statemon import DNS


class DnsChecker(AbstractChecker):
    """Domain Name Service"""
    TYPENAME = "dns"
    IPV6_SUPPORT = True
    DESCRIPTION = "Domain Name Service"
    ARGS = (
        ('request', ''),
    )
    OPTARGS = (
        ('port', ''),
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        """Please note that this handler doesn't obey the port directive"""
        AbstractChecker.__init__(self, service, port=42, **kwargs)

    def execute(self):
        ip, _port = self.getAddress()
        dns = DNS.DnsRequest(server=ip, timeout=self.getTimeout())
        args = self.getArgs()

        request = args.get("request", "").strip()
        timeout = 0
        if not request:
            return Event.UP, "Argument request must be supplied"
        else:
            answer = ""
            try:
                reply = dns.req(name=request)
            except DNS.Error:
                timeout = 1

            if not timeout and len(reply.answers) > 0:
                answer = 1
            elif not timeout and len(reply.answers) == 0:
                answer = 0

            # This breaks on windows dns servers and probably other not bind
            # servers. We just put a exception handler around it, and ignore
            # the resulting timeout.
            try:
                ver = dns.req(name="version.bind", qclass="chaos",
                              qtype='txt').answers
                if len(ver) > 0:
                    self.setVersion(ver[0]['data'][0])
            except DNS.Base.DNSError as err:
                if str(err) == 'Timeout':
                    pass  # Ignore timeout
                else:
                    raise            

            if not timeout and answer == 1:
                return Event.UP, "Ok"
            elif not timeout and answer == 0:
                return Event.UP, "No record found, request=%s" % request
            else:
                return Event.DOWN, "Timeout while requesting %s" % request
