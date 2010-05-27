# -*- coding: utf-8 -*-
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

import socket
import imaplib

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import  Event

class IMAPConnection(imaplib.IMAP4):
    def __init__(self, timeout, host, port):
        self.timeout=timeout
        imaplib.IMAP4.__init__(self, host, port)

    def open(self, host, port):
        """
        Overload imaplib's method to connect to the server
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "imap", service, port=143, **kwargs)
    def execute(self):
        args = self.getArgs()
        user = args.get("username","")
        ip, port = self.getAddress()
        passwd = args.get("password","")
        m = IMAPConnection(self.getTimeout(), ip, port)
        ver = m.welcome
        if user:
            m.login(user, passwd)
            m.logout()
        version=''
        ver=ver.split(' ')
        if len(ver) >= 2:
            for i in ver[2:]:
                if i != "at":
                    version += "%s " % i
                else:
                    break
        self.setVersion(version)
        
        return Event.UP, version

def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = ['username', 'password']
    return requiredArgs

