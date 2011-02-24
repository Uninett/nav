from unittest import TestCase
from minimock import Mock

from nav.web.netmap.views import output_graph_data


class NetmapServerTest(TestCase):
    def test_server_no_unicode_output(self):
        request = Mock('request')
        request.build_absolute_uri = lambda: '/netmap/server'
        request._req = Mock('ModPythonRequest')
        request._req.session = {'user': {'login': 'admin'}}

        response = output_graph_data(request)
        self.assertNotEquals(type(response.content), unicode)
