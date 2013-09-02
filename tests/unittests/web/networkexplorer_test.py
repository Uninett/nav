from django.utils.unittest import TestCase
from django.test.client import RequestFactory

from nav.web.networkexplorer.forms import NetworkSearchForm
from nav.web.networkexplorer.views import (
    IndexView,
    RouterJSONView,
    SearchView,
)


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

        self.assertEqual(response.status_code, 200)
        self.assertTrue('routers' in response.content)
        self.assertTrue('gwports' in response.content)
        self.assertTrue('swports' in response.content)

    def test_search_view_with_invalid_query(self):
        request = self.factory.get(
            self.url_root + 'search/',
            self.invalid_data,
        )
        response = SearchView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertFalse('routers' in response.content)
        self.assertFalse('gwports' in response.content)
        self.assertFalse('swports' in response.content)


class FormsTest(TestDataMixin, TestCase):

    def test_search_form(self):

        valid_form = NetworkSearchForm(self.valid_data)
        invalid_form = NetworkSearchForm(self.invalid_data)

        self.assertTrue(
            valid_form.is_valid(),
            msg='Valid form failed validaion')
        self.assertFalse(
            invalid_form.is_valid(),
            msg='Invalid form passed validation')