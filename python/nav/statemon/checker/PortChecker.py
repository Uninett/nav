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
"""Simple TCP port service checker"""

import select
import socket

from nav.statemon.abstractchecker import AbstractChecker
from nav.statemon.event import Event


class PortChecker(AbstractChecker):
    """Generic TCP port checker"""

    IPV6_SUPPORT = True
    DESCRIPTION = "Generic port checker"
    ARGS = (('port', ''),)

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=23, **kwargs)

    def execute(self):
        sock = socket.create_connection(self.get_address(), self.timeout)
        sockfile = sock.makefile('r')
        _readable, __w, __x = select.select([sock], [], [], self.timeout)
        if _readable:
            sockfile.readline()
        status = Event.UP
        txt = 'Alive'
        sock.close()

        return status, txt
