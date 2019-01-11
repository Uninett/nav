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
"""FTP Service Checker"""
import socket
import ftplib

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class FtpChecker(AbstractChecker):
    """File Transfer Protocol"""
    DESCRIPTION = "FTP"
    OPTARGS = (
        ('username', ''),
        ('password', ''),
        ('path', ''),
    )
    IPV6_SUPPORT = True

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=0, **kwargs)

    def execute(self):
        session = FTP(self.timeout)
        ip, port = self.get_address()
        output = session.connect(ip, port or 21)

        # Get server version from the banner.
        version = ''
        for line in session.welcome.split('\n'):
            if line.startswith('220 '):
                version = line[4:].strip()
        self.version = version

        username = self.args.get('username', '')
        password = self.args.get('password', '')
        path = self.args.get('path', '')
        output = session.login(username, password, path)

        if output[:3] == '230':
            return Event.UP, 'code 230'
        else:
            return Event.DOWN, output.split('\n')[0]


# pylint: disable=R0913,W0221,R0904
class FTP(ftplib.FTP):
    """Customized FTP protocol interface"""
    def __init__(self, timeout, host='', user='', passwd='', acct=''):
        ftplib.FTP.__init__(self)
        if host:
            self.connect(host)
        if user:
            self.login(user, passwd, acct)
        self.timeout = timeout

    def connect(self, host='', port=0):
        """Connects to host.

        :param host: hostname to connect to (string, default previous host)
        :param port: port to connect to (integer, default previous port)

        """
        if host:
            self.host = host
        if port:
            self.port = port
        self.sock = socket.create_connection((self.host, self.port),
                                             self.timeout)
        self.file = self.sock.makefile('rb')
        self.welcome = self.getresp()
        return self.welcome
