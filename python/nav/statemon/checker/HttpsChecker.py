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

import sys
import httplib
import socket
from urlparse import urlsplit
from nav.statemon.event import Event
from nav.statemon.abstractChecker import AbstractChecker

class HTTPSConnection(httplib.HTTPSConnection):
    def __init__(self, timeout, host, port=443):
        httplib.HTTPSConnection.__init__(self, host, port)
        self.timeout = timeout
        self.connect()
    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))
        ssl = socket.ssl(self.sock, None, None)
        self.sock = httplib.FakeSocket(self.sock, ssl)
        
class HttpsChecker(AbstractChecker):
    def __init__(self, service, **kwargs):
        AbstractChecker.__init__(self, "https", service, port=0, **kwargs)
    def execute(self):
        ip, port = self.getAddress()
        args = self.getArgs()
        url = args.get('url','')
        username = args.get('username')
        password = args.get('password','')
        if not url:
            url = "/"
        protocol, vhost, path, query, fragment = urlsplit(url)
        
        i = HTTPSConnection(self.getTimeout(), ip, port or 443)

        if vhost:
            i.host = vhost

        if '?' in url:
            path = path + '?' + query
        i.putrequest('GET', path)
        internalRev = "$Rev: 1361 $"
        internalRev = internalRev[:-2].replace('$Rev: ','')
        i.putheader('User-Agent','NAV/ServiceMon Build 1734 Release 31337, internal revision %s' % internalRev)
        if username:
            auth = "%s:%s" % (username, password)
            i.putheader("Authorization", "Basic %s" % auth.encode("base64"))
        i.endheaders()
        response = i.getresponse()
        if response.status >= 200 and response.status < 400:
            status = Event.UP
            version = response.getheader('SERVER')
            self.setVersion(version)
            info = 'OK (%s) %s' % (str(response.status), version)
        else:
            status = Event.DOWN
            info = 'ERROR (%s) %s'  % (str(response.status), url)

        return status, info
