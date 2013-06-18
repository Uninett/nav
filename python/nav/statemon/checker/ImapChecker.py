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
"""IMAP service checker"""

import socket
import imaplib
from nav.statemon.DNS import socktype_from_addr

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import  Event


# pylint: disable=R0904
class IMAPConnection(imaplib.IMAP4):
    """Customized IMAP protocol interface"""
    def __init__(self, timeout, host, port):
        self.timeout = timeout
        imaplib.IMAP4.__init__(self, host, port)

    # pylint: disable=W0222
    def open(self, host, port):
        self.sock = socket.socket(socktype_from_addr(host), socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((host, port))
        self.file = self.sock.makefile("rb")

class ImapChecker(AbstractChecker):
    """
    Valid arguments:
    port
    username
    password
    """
    TYPENAME = "imap"
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
        args = self.getArgs()
        user = args.get("username", "")
        ip, port = self.getAddress()
        passwd = args.get("password", "")
        session = IMAPConnection(self.getTimeout(), ip, port)
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
        self.setVersion(version)
        
        return Event.UP, version
