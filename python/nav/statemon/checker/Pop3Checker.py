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
import poplib

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event

class PopConnection(poplib.POP3):
    def __init__(self, timeout, ip, port):
        self.ip=ip
        self.port=port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((self.ip, self.port))
        self.file = self.sock.makefile('rb')
        self._debugging=0
        self.welcome = self._getresp()


class Pop3Checker(AbstractChecker):
    """
    args:
    username
    password
    port
    """
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "pop3", service, port=110, **kwargs)
    def execute(self):
        args = self.getArgs()
        user = args.get("username","")
        passwd = args.get("password", "")
        ip, port = self.getAddress()
        p = PopConnection(self.getTimeout(), ip, port)
        ver = p.getwelcome()
        if user:
            p.user(user)
            p.pass_(passwd)
            nummessages = len(p.list()[1])
            p.quit()
        version = ''
        ver=ver.split(' ')
        if len(ver) >= 1:
            for i in ver[1:]:
                if i != "server":
                    version += "%s " % i
                else:
                    break
        self.setVersion(version)
                
        return Event.UP, version
