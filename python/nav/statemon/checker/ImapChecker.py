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
"""IMAP service checker"""

import contextlib
import socket
import imaplib

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class IMAPConnection(imaplib.IMAP4):
    """Customized IMAP protocol interface"""

    def __init__(self, timeout, host, port):
        self.timeout = timeout
        imaplib.IMAP4.__init__(self, host, port)

    def open(self, host, port):
        self.sock = socket.create_connection((host, port), self.timeout)
        self.file = self.sock.makefile("rb")


class ImapChecker(AbstractChecker):
    """
    Valid arguments:
    port
    username
    password
    """

    IPV6_SUPPORT = True
    DESCRIPTION = "Internet mail application protocol"
    ARGS = (
        ('username', ''),
        ('password', ''),
    )
    OPTARGS = (
        ('port', ''),
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=143, **kwargs)

    def execute(self):
        user = self.args.get("username", "")
        ip, port = self.get_address()
        passwd = self.args.get("password", "")
        with contextlib.closing(IMAPConnection(self.timeout, ip, port)) as session:
            ver = session.welcome
            if user:
                session.login(user, passwd)
                session.logout()
            version = ''
            ver = ver.split(' ')
            if len(ver) >= 2:
                for i in ver[2:]:
                    if i != "at":
                        version += "%s " % i
                    else:
                        break
            self.version = version

            return Event.UP, version
