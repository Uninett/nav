from unittest import TestCase
from minimock import Mock

class ModPythonTestCase(TestCase):
    module_under_test = None

    def setUp(self):
        super(ModPythonTestCase, self).setUp()
        # yes, modifying global state is all the rage these days
        self.user = {'login': u'admin', 'id': 1}
        from nav.web.templates.MainTemplate import MainTemplate
        MainTemplate.user = self.user
        self.module_under_test.apache = Mock('apache')
        self.module_under_test.apache.OK = 200

    def make_request(self, uri):
        """Returns a mocked mod_python request object for the given uri."""
        request = Mock('request')
        request.uri = uri
        request.unparsed_uri = uri
        request.filename = uri.endswith('/') and uri[:-1] or uri

        request.hostname = 'localhost'
        request.is_https = lambda: True
        request.session = {'user': self.user}
        request.headers_in = {'cookie': 'nav_sessid=xxx'}
        request.args = ''
        return request

    def handler_outputs_no_unicode(self, uri):
        request = self.make_request(uri)
        request.write = lambda s: self.assertNotEquals(type(s), unicode)
        self.assertEquals(self.module_under_test.handler(request), 200)

