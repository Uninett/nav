from unittest import TestCase
from mock import Mock

from nav.web.netmap.views import output_graph_data


class NetmapServerTest(TestCase):
    def test_server_no_unicode_output(self):
        request = Mock()
        request.build_absolute_uri.return_value = '/netmap/server'
        request._req = Mock(session={'user': {'login': 'admin'}})

        response = output_graph_data(request)
        self.assertNotEquals(type(response.content), unicode)
