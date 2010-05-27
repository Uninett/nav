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

import re
import socket
import smtplib

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event

class SMTP(smtplib.SMTP):
    def __init__(self,timeout, host = '',port = 25):
        self._timeout = timeout  # _ to avoid name collision with superclass
        smtplib.SMTP.__init__(self,host,port)
    def connect(self, host='localhost', port = 25):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self._timeout)
        self.sock.connect((host,port))
        return self.getreply()

class SmtpChecker(AbstractChecker):
    # Regexp for matching version strings:
    # Most SMTP servers add a date after one of the characters
    # ",", ";" or "#", we don't need that part of the version
    # string
    versionMatch = re.compile(r'([^;,#]+)')
    
    def __init__(self,service, **kwargs):
        AbstractChecker.__init__(self, "smtp", service,port=25, **kwargs)
    def execute(self):
        ip,port = self.getAddress()
        s = SMTP(self.getTimeout())
        code,msg = s.connect(ip,port)
        try:
            s.quit()
        except smtplib.SMTPException:
            pass
        if code != 220:
            return Event.DOWN,msg
        try:
            domain, version = msg.strip().split(' ', 1)
        except ValueError:
            version = ''
        match = self.versionMatch.match(version)
        if match:
            version = match.group(0)
        self.setVersion(version)
        return Event.UP,msg

def getRequiredArgs():
    """
    Returns a list of required arguments
    """
    requiredArgs = []
    return requiredArgs

