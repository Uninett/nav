from unittest import TestCase
from nav.web.netmap.views import traffic_load_gradient
from django.test.client import RequestFactory


class NetmapViewtests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()

    def test_api_traffic_load_gradient_gets_successful_response_code(self):
        request = self.rf.get('/netmap/api/traffic_load_gradient')
        response = traffic_load_gradient(request)
        assert response.status_code == 200

    def test_api_traffic_load_gradient_contains_101_rgb_values(self):
        request = self.rf.get('/netmap/api/traffic_load_gradient')
        response = traffic_load_gradient(request)
        import simplejson
        # from 0 % to 100% , 101 entries.
        assert len(simplejson.loads(response.content)) == 101