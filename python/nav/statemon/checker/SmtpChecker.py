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
"""SMTP service checker"""
import re
import socket
import smtplib
from nav.statemon.DNS import socktype_from_addr

from nav.statemon.abstractChecker import AbstractChecker
from nav.statemon.event import Event


class SmtpChecker(AbstractChecker):
    """SMTP"""
    TYPENAME = "smtp"
    IPV6_SUPPORT = True
    DESCRIPTION = "Simple mail transport protocol"
    OPTARGS = (
        ('port', ''),
        ('timeout', ''),
    )

    VERSION_PATTERN = re.compile(r'([^;,#]+)')

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=25, **kwargs)

    def execute(self):
        ip, port = self.getAddress()
        smtp = SMTP(self.getTimeout())
        code, msg = smtp.connect(ip, port)
        try:
            smtp.quit()
        except smtplib.SMTPException:
            pass
        if code != 220:
            return Event.DOWN, msg
        try:
            _domain, version = msg.strip().split(' ', 1)
        except ValueError:
            version = ''
        match = self.VERSION_PATTERN.match(version)
        if match:
            version = match.group(0)
        self.setVersion(version)
        return Event.UP, msg


#pylint: disable=R0904
class SMTP(smtplib.SMTP):
    """A customized SMTP protocol interface"""
    def __init__(self, timeout, host='', port=25):
        self._timeout = timeout  # _ to avoid name collision with superclass
        smtplib.SMTP.__init__(self, host, port)

    def connect(self, host='localhost', port = 25):
        self.sock = socket.socket(socktype_from_addr(host), socket.SOCK_STREAM)
        self.sock.settimeout(self._timeout)
        self.sock.connect((host, port))
        return self.getreply()
