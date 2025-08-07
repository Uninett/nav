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
"""POP3 service checker"""

import socket
import poplib

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class Pop3Checker(AbstractChecker):
    """Post office protocol"""

    IPV6_SUPPORT = True
    DESCRIPTION = "Post office protocol"
    ARGS = (
        ('username', ''),
        ('password', ''),
    )
    OPTARGS = (
        ('port', ''),
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=110, **kwargs)

    def execute(self):
        user = self.args.get("username", "")
        passwd = self.args.get("password", "")
        ip, port = self.get_address()
        conn = PopConnection(self.timeout, ip, port)
        try:
            ver = conn.getwelcome()
            if user:
                conn.user(user)
                conn.pass_(passwd)
                len(conn.list()[1])
            version = ''
            ver = ver.split(' ')
            if len(ver) >= 1:
                for i in ver[1:]:
                    if i != "server":
                        version += "%s " % i
                    else:
                        break
            self.version = version
        finally:
            conn.quit()

        return Event.UP, version


class PopConnection(poplib.POP3):
    """Customized POP3 protocol interface"""

    def __init__(self, timeout, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.create_connection((self.ip, self.port), timeout)
        self.file = self.sock.makefile('rb')
        self._debugging = 0
        self.welcome = self._getresp()
