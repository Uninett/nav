import sys
from unittest import TestCase
from minimock import Mock

from nav.web.netmap import handler

class NetmapServerTest(TestCase):
    def setUp(self):
        # yes, modifying global state is all the rage these days
        self.user = {'login': 'admin', 'id': 1}
        from nav.web.templates.MainTemplate import MainTemplate
        MainTemplate.user = self.user
        handler.apache = Mock('apache')
        handler.apache.OK = 200

    def test_server_no_unicode_output(self):
        request = Mock('request')
        request.uri = '/netmap/server/'
        request.unparsed_uri = request.uri
        request.filename = '/netmap/server'

        request.hostname = 'localhost'
        request.is_https = lambda: True
        request.session = {'user': self.user}
        request.headers_in = {'cookie': 'nav_sessid=xxx'}

        request.write = lambda s: self.assertEquals(type(s), str)
        self.assertEquals(handler.handler(request), 200)
