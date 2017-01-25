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
"""HTTPS Service checker"""

import httplib
import socket
from urlparse import urlsplit
from nav import buildconf
from nav.statemon.event import Event
from nav.statemon.abstractchecker import AbstractChecker

from ssl import wrap_socket


class HTTPSConnection(httplib.HTTPSConnection):
    """Customized HTTPS protocol interface"""
    def __init__(self, timeout, host, port=443):
        httplib.HTTPSConnection.__init__(self, host, port)
        self.timeout = timeout
        self.connect()

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port),
                                             self.timeout)
        self.sock = wrap_socket(self.sock)


class HttpsChecker(AbstractChecker):
    """HTTPS"""
    IPV6_SUPPORT = True
    DESCRIPTION = "HTTPS"
    OPTARGS = (
        ('url', ''),
        ('username', ''),
        ('password', ''),
        ('port', ''),
        ('timeout', ''),
    )

    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, service, port=0, **kwargs)

    def execute(self):
        ip, port = self.get_address()
        url = self.args.get('url', '')
        username = self.args.get('username')
        password = self.args.get('password', '')
        if not url:
            url = "/"
        _protocol, vhost, path, query, _fragment = urlsplit(url)

        i = HTTPSConnection(self.timeout, ip, port or 443)

        if vhost:
            i.host = vhost

        if '?' in url:
            path = path + '?' + query
        i.putrequest('GET', path)
        i.putheader('User-Agent',
                    'NAV/servicemon; version %s' % buildconf.VERSION)
        if username:
            auth = "%s:%s" % (username, password)
            i.putheader("Authorization", "Basic %s" % auth.encode("base64"))
        i.endheaders()
        response = i.getresponse()
        if 200 <= response.status < 400:
            status = Event.UP
            version = response.getheader('SERVER')
            self.version = version
            info = 'OK (%s) %s' % (str(response.status), version)
        else:
            status = Event.DOWN
            info = 'ERROR (%s) %s' % (str(response.status), url)

        return status, info
