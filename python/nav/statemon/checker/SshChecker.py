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
"""SSH service checker"""

import socket

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class SshChecker(AbstractChecker):
    """Checks for SSH availability"""

    IPV6_SUPPORT = True
    DESCRIPTION = "Secure shell server"
    OPTARGS = (
        ('port', ''),
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=22, **kwargs)

    def execute(self):
        (hostname, port) = self.get_address()
        try:
            sock = socket.create_connection((hostname, port), self.timeout)
            stream = sock.makefile('rw')
            version = stream.readline().strip()
            protocol, major = version.split('-')[:2]
            stream.write("%s-%s-%s\r\n" % (protocol, major, "NAV_Servicemon"))
            stream.flush()
        except Exception as err:  # noqa: BLE001
            return (
                Event.DOWN,
                "Failed to send version reply to %s: %s"
                % (self.get_address(), str(err)),
            )
        finally:
            try:
                sock.close()
            except UnboundLocalError:
                pass  # sock was never created
        self.version = version
        return Event.UP, version
