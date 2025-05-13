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

import contextlib
from ftplib import FTP

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
        with contextlib.closing(FTP(timeout=self.timeout)) as session:
            ip, port = self.get_address()
            welcome = session.connect(ip, port or 21)

            # This cannot happen on Linux (debian)
            # A bug has been reported on FreeBSD so we CYA
            if isinstance(welcome, bytes):
                welcome = welcome.decode('utf-8', 'replace')

            # Get server version from the banner.
            version = ''
            for line in welcome.split('\n'):
                if line.startswith('220 '):
                    version = line.removeprefix('220 ').strip()
            self.version = version

            username = self.args.get('username', '')
            password = self.args.get('password', '')
            path = self.args.get('path', '')
            output = session.login(username, password, path)

            if output[:3] == '230':
                return Event.UP, 'code 230'
            else:
                return Event.DOWN, output.split('\n')[0]
