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
"""HTTPS Service checker"""

from django.utils.six.moves import http_client
import socket

from ssl import wrap_socket

from nav.statemon.checker.HttpChecker import HttpChecker


class HTTPSConnection(http_client.HTTPSConnection):
    """Customized HTTPS protocol interface"""
    def __init__(self, timeout, host, port=443):
        http_client.HTTPSConnection.__init__(self, host, port)
        self.timeout = timeout
        self.connect()

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port),
                                             self.timeout)
        self.sock = wrap_socket(self.sock)


class HttpsChecker(HttpChecker):
    """HTTPS"""
    PORT = 443

    def connect(self, ip, port):
        return HTTPSConnection(self.timeout, ip, port)
