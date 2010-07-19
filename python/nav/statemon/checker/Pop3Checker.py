# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# $Id$
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event
from nav.statemon import Socket
import poplib
class PopConnection(poplib.POP3):
    def __init__(self, timeout, ip, port):
        self.ip=ip
        self.port=port
        self.sock=Socket.Socket(timeout)
        self.sock.connect((self.ip, self.port))
        self.file=self.sock.makefile('rb')
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

def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = ['username', 'password']
    return requiredArgs

