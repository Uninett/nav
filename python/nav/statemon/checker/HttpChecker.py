#
# Copyright (C) 2018, 2020 Uninett AS
# Copyright (C) 2022 Sikt
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
"""HTTP Service Checker"""

import contextlib
import socket
import base64
import http.client

from urllib.parse import urlsplit

from nav import buildconf
from nav.statemon.event import Event
from nav.statemon.abstractchecker import AbstractChecker


class HTTPConnection(http.client.HTTPConnection):
    """Customized HTTP protocol interface"""

    def __init__(self, timeout, host, port=80):
        http.client.HTTPConnection.__init__(self, host, port)
        self.timeout = timeout
        self.connect()

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), self.timeout)


class HttpChecker(AbstractChecker):
    """HTTP"""

    IPV6_SUPPORT = True
    DESCRIPTION = "HTTP"
    OPTARGS = (
        ('url', ''),
        ('username', ''),
        ('password', ''),
        ('port', ''),
        ('timeout', ''),
    )
    PORT = 80

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=0, **kwargs)

    def connect(self, ip, port):
        return HTTPConnection(self.timeout, ip, port)

    def execute(self):
        ip, port = self.get_address()
        url = self.args.get('url', '/')
        username = self.args.get('username')
        password = self.args.get('password', '')
        _protocol, vhost, path, query, _fragment = urlsplit(url)
        if ':' in vhost:
            vhost, port = vhost.split(':', 1)
            port = int(port)

        with contextlib.closing(self.connect(ip, port or self.PORT)) as i:
            if vhost:
                i.host = vhost

            if '?' in url:
                path = path + '?' + query
            i.putrequest('GET', path)
            i.putheader('User-Agent', 'NAV/servicemon; version %s' % buildconf.VERSION)
            if username:
                auth = "{}:{}".format(username, password).encode("utf-8")
                auth = base64.b64encode(auth).decode("utf-8")
                i.putheader("Authorization", "Basic {}".format(auth))
            i.endheaders()
            response = i.getresponse()
            if 200 <= response.status < 400 or (
                response.status == 401 and not username
            ):
                status = Event.UP
                version = response.getheader('SERVER')
                self.version = version
                info = 'OK (%s) %s' % (str(response.status), version)
            else:
                status = Event.DOWN
                info = 'ERROR (%s) %s' % (str(response.status), url)

            return status, info
