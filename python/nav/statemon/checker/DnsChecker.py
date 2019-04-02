#
# Copyright (C) 2018 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""DNS service checker"""

import socket

import dns.exception
import dns.message
import dns.query

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class DnsChecker(AbstractChecker):
    """Domain Name Service"""
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
        ip, _port = self.get_address()
        request = self.args.get("request", "").strip()
        timeout = False
        error = False
        if not request:
            return Event.UP, "Argument request must be supplied"
        else:
            answer = ""
            try:
                query = dns.message.make_query(request, "ANY")
                reply = dns.query.udp(query, ip, timeout=self.timeout)
            except dns.exception.Timeout:
                timeout = True
                error = True
            except socket.error:
                error = True

            if not error and reply.rcode() != dns.rcode.NOERROR:
                error = True

            if not error and len(reply.answer) > 0:
                answer = 1
            elif not error and len(reply.answer) == 0:
                answer = 0

            # This breaks on windows dns servers and probably other not bind
            # servers. We just put a exception handler around it, and ignore
            # the resulting timeout.
            try:
                query = dns.message.make_query("version.bind", rdclass="CH",
                                               rdtype='txt')
                response = dns.query.udp(query, ip, timeout=self.timeout)
                if (response.rcode() == dns.rcode.NOERROR and
                        len(response.answer) > 1):
                    self.version = response.answer[0][0]
            except dns.exception.Timeout:
                pass

            if not error and answer == 1:
                return Event.UP, "Ok"
            elif not error and answer == 0:
                return Event.UP, "No record found, request=%s" % request
            elif error and not timeout:
                return Event.DOWN, "Other error while requesting %s" % request
            else:
                return Event.DOWN, "Timeout while requesting %s" % request
