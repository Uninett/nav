from unittest import TestCase
from nav.web.networkexplorer import search
from nav.web.networkexplorer.forms import NetworkSearchForm
from nav.web.networkexplorer.views import (
    IndexView,
    RouterJSONView,
    SearchView,
)

from django.test.client import RequestFactory


class NetworkExplorerSearchTest(TestCase):
    """Tests that the various network explorer search functions don't raise
    database exceptions.

    Will not cover all code paths on an empty database.

    """

    def test_search_expand_swport(self):
        search.search_expand_swport(1)

    def test_search_expand_netbox(self):
        search.search_expand_netbox(1)

    def test_search_expand_sysname(self):
        search.search_expand_sysname('foo-gw.example.org')

    def test_search_expand_mac(self):
        search.search_expand_mac('00:12:34:56:78:90')

    def test_sysname_search(self):
        search.sysname_search('foo-gw.example.org')

    def test_ip_search(self):
        search.ip_search('10.0.1')

    def test_ip_search_exact(self):
        search.ip_search('10.0.1.0', exact=True)

    def test_portname_search(self):
        search.portname_search('KX182')

    def test_portname_search_exact(self):
        search.portname_search('KX182', exact=True)

    def test_room_search(self):
        search.room_search('myroom')

    def test_room_search_exact(self):
        search.room_search('myroom', exact=True)

    def test_mac_search(self):
        search.mac_search('00:12:34:56:78:90')

    def test_vlan_search(self):
        search.vlan_search('20')

    def test_vlan_search_exact(self):
        search.vlan_search('20', exact=True)


class TestDataMixin(object):
    valid_data = {
        'query_0': 'somequery',
        'query_1': 'sysname',
    }
    invalid_data = {
        'query_0': 'somequery',
        # Missing query type
    }


class ViewsTest(TestDataMixin, TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.url_root = '/networkexplorer/'

    def test_index_view(self):
        request = self.factory.get(self.url_root)
        response = IndexView.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_router_json_view(self):
        request = self.factory.get(self.url_root + 'routers/')
        response = RouterJSONView.as_view()(request)

        self.assertEqual(response.status_code, 200)

    def test_search_view_with_valid_query(self):
        request = self.factory.get(
            self.url_root + 'search/',
            self.valid_data,
        )
        response = SearchView.as_view()(request)
        content = response.content.decode('utf-8')

        self.assertEqual(response.status_code, 200)
        self.assertTrue('routers' in content)
        self.assertTrue('gwports' in content)
        self.assertTrue('swports' in content)

    def test_search_view_with_invalid_query(self):
        request = self.factory.get(
            self.url_root + 'search/',
            self.invalid_data,
        )
        response = SearchView.as_view()(request)
        content = response.content.decode('utf-8')

        self.assertEqual(response.status_code, 400)
        self.assertFalse('routers' in content)
        self.assertFalse('gwports' in content)
        self.assertFalse('swports' in content)

    def test_search_view_will_return_status_400_on_invalid_exact_ip_search(self):
        request = self.factory.get(
            self.url_root + 'search/',
            {
                'query_0': 'invalid',
                'query_1': 'ip',
                'exact_results': 'on',
            },
        )
        response = SearchView.as_view()(request)
        content = response.content.decode('utf-8')

        assert response.status_code == 400
        assert "Invalid IP address" in content


class FormsTest(TestDataMixin, TestCase):
    def test_search_form_with_valid_data_is_valid(self):
        valid_form = NetworkSearchForm(self.valid_data)

        self.assertTrue(valid_form.is_valid(), msg='Valid form failed validaion')

    def test_search_form_with_missing_argument_is_invalid(self):
        invalid_form = NetworkSearchForm(self.invalid_data)

        self.assertFalse(invalid_form.is_valid(), msg='Invalid form passed validation')

    def test_search_form_with_invalid_ip_for_exact_search_is_invalid(self):
        invalid_ip_form = NetworkSearchForm(
            {
                "query_0": "invalid_ip",
                "query_1": "ip",
                "exact_results": True,
            }
        )

        self.assertFalse(
            invalid_ip_form.is_valid(), msg="Invalid IP form passed validation"
        )
