from datetime import datetime
from urllib.parse import urlencode

import pytest
from django.urls import reverse
from django.utils.encoding import smart_str
from mock import MagicMock, patch


class TestAccountLogSearch:
    def test_all_time_search_should_return_no_results_for_no_entries(
        db, client, admin_username
    ):
        url = reverse('radius-account_search')
        params = {
            'query_0': 'username',
            'query_1': admin_username,
            'time_0': '',
            'port_type': '',
            'send': 'Search',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'No results' in smart_str(response.content)

    def test_day_search_should_return_no_results_for_no_entries(
        db, client, admin_username
    ):
        url = reverse('radius-account_search')
        params = {
            'query_0': 'username',
            'query_1': admin_username,
            'time_0': 'days',
            'time_1': 3,
            'port_type': '',
            'send': 'Search',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'No results' in smart_str(response.content)

    def test_day_search_should_not_crash_on_big_days(db, client, admin_username):
        url = reverse('radius-account_search')
        params = {
            'query_0': 'username',
            'query_1': admin_username,
            'time_0': 'days',
            'time_1': 123123123123123,
            'port_type': '',
            'send': 'Search',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'They did not have computers' in smart_str(response.content)

    def test_timespan_search_should_return_no_results_for_no_entries(
        db, client, admin_username
    ):
        url = reverse('radius-account_search')
        params = {
            'query_0': 'username',
            'query_1': admin_username,
            'time_0': 'timestamp',
            'time_1': '2025-09-05 09:06|1440',
            'port_type': '',
            'send': 'Search',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'No results' in smart_str(response.content)


class TestErrorLogSearch:
    def test_all_time_search_should_return_no_result_for_no_entries(
        db, client, admin_username
    ):
        url = reverse('radius-log_search')
        params = {
            'query_0': 'username',
            'query_1': admin_username,
            'log_entry_type': '',
            'time_0': '',
            'send': 'Search',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'No result' in smart_str(response.content)

    def test_hour_search_should_return_no_result_for_no_entries(
        db, client, admin_username
    ):
        url = reverse('radius-log_search')
        params = {
            'query_0': 'username',
            'query_1': admin_username,
            'log_entry_type': '',
            'time_0': 'hours',
            'time_1': 3,
            'send': 'Search',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'No result' in smart_str(response.content)

    def test_hour_search_should_not_crash_on_big_hours(db, client, admin_username):
        url = reverse('radius-log_search')
        params = {
            'query_0': 'username',
            'query_1': admin_username,
            'log_entry_type': '',
            'time_0': 'hours',
            'time_1': 123123123123123,
            'send': 'Search',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'They did not have computers' in smart_str(response.content)

    def test_timespan_search_should_return_no_result_for_no_entries(
        db, client, admin_username
    ):
        url = reverse('radius-log_search')
        params = {
            'query_0': 'username',
            'query_1': admin_username,
            'log_entry_type': '',
            'time_0': 'timestamp',
            'time_1': '2025-09-05 09:06|1440',
            'send': 'Search',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'No result' in smart_str(response.content)


class TestTopTalkers:
    def test_day_search_should_return_tables_with_top_talkers(db, client):
        url = reverse('radius-account_charts')
        params = {
            'days': 7,
            'charts': 'sentrecv',
            'send': 'Show me',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'Bandwidth Hogs (Upload+Downloads)' in smart_str(response.content)

    def test_day_search_should_not_crash_on_big_days(db, client):
        url = reverse('radius-account_charts')
        params = {
            'days': 123123123123,
            'charts': 'sentrecv',
            'send': 'Show me',
        }
        url = url + '?' + urlencode(params)
        response = client.get(url)

        assert response.status_code == 200
        assert 'They did not have computers' in smart_str(response.content)


class TestRadiusSearchHintModalViews:
    def test_should_render_account_log_hints_modal(self, db, client):
        url = reverse('radius-account-log-hints')
        response = client.get(url)

        assert response.status_code == 200
        assert 'id="account-log-hints"' in smart_str(response.content)

    def test_should_render_error_log_hints_modal(self, db, client):
        url = reverse('radius-error-log-hints')
        response = client.get(url)

        assert response.status_code == 200
        assert 'id="error-log-hints"' in smart_str(response.content)

    def test_should_render_account_chart_hints_modal(self, db, client):
        url = reverse('radius-account-chart-hints')
        response = client.get(url)

        assert response.status_code == 200
        assert 'id="account-chart-hints"' in smart_str(response.content)


class TestRadiusAccountDetailViews:
    @patch('nav.web.radius.views.AcctDetailQuery')
    def test_should_render_account_detail_page(
        self, mock_query_class, db, client, mock_account_detail_query
    ):
        mock_query_class.return_value = mock_account_detail_query()

        url = reverse('radius-account_detail', args=[1])
        response = client.get(url)

        assert response.status_code == 200
        assert 'Account Detail' in smart_str(response.content)
        assert 'navpath' in response.context

    @patch('nav.web.radius.views.AcctDetailQuery')
    def test_should_render_account_detail_modal(
        self, mock_query_class, db, client, mock_account_detail_query
    ):
        mock_query_class.return_value = mock_account_detail_query()

        url = reverse('radius-account_detail-modal', args=[1])
        response = client.get(url)

        assert response.status_code == 200
        assert 'id="account-detail"' in smart_str(response.content)
        assert (
            'navpath' not in response.context or response.context.get('navpath') is None
        )

    @patch('nav.web.radius.views.AcctDetailQuery')
    def test_account_detail_handles_empty_result(self, mock_query_class, db, client):
        # Override for empty result test
        mock_query = MagicMock()
        mock_query.result = []
        mock_query_class.return_value = mock_query

        url = reverse('radius-account_detail', args=[999])
        response = client.get(url)

        assert "No details available" in smart_str(response.content)

    @patch('nav.web.radius.views.AcctDetailQuery')
    def test_with_custom_username(
        self, mock_query_class, db, client, mock_account_detail_query
    ):
        # Example of customizing the mock data
        mock_query_class.return_value = mock_account_detail_query(
            {'username': 'custom_user'}
        )

        url = reverse('radius-account_detail', args=[1])
        response = client.get(url)

        assert response.status_code == 200


class TestRadiusLogDetailViews:
    @patch('nav.web.radius.views.LogDetailQuery')
    def test_should_render_log_detail_page(
        self, mock_query_class, db, client, mock_log_detail_query
    ):
        mock_query_class.return_value = mock_log_detail_query()

        url = reverse('radius-log_detail', args=[1])
        response = client.get(url)

        assert response.status_code == 200
        assert 'Log Detail' in smart_str(response.content)
        assert 'navpath' in response.context

    @patch('nav.web.radius.views.LogDetailQuery')
    def test_should_render_log_detail_modal(
        self, mock_query_class, db, client, mock_log_detail_query
    ):
        mock_query_class.return_value = mock_log_detail_query()

        url = reverse('radius-log_detail-modal', args=[1])
        response = client.get(url)

        assert response.status_code == 200
        assert 'id="log-detail"' in smart_str(response.content)
        assert (
            'navpath' not in response.context or response.context.get('navpath') is None
        )

    @patch('nav.web.radius.views.LogDetailQuery')
    def test_log_detail_handles_empty_result(self, mock_query_class, db, client):
        mock_query = MagicMock()
        mock_query.result = []
        mock_query_class.return_value = mock_query

        url = reverse('radius-log_detail', args=[999])
        response = client.get(url)

        assert "No details available" in smart_str(response.content)

    @patch('nav.web.radius.views.LogDetailQuery')
    def test_log_detail_with_custom_message(
        self, mock_query_class, db, client, mock_log_detail_query
    ):
        mock_query_class.return_value = mock_log_detail_query(
            {'message': 'Custom [error] message', 'type': 'Auth-Reject'}
        )

        url = reverse('radius-log_detail', args=[1])
        response = client.get(url)

        assert response.status_code == 200


@pytest.fixture
def mock_account_detail_query():
    """Factory fixture for creating mocked AcctDetailQuery"""

    def _create_mock(custom_attributes=None):
        mock_result = MagicMock()

        default_attributes = {
            'acctuniqueid': '1309f5d67b0a752d',
            'username': 'test_user',
            'nasipaddress': '192.168.1.1 (test-nas.example.com)',
            'framedipaddress': '10.0.0.1 (10.0.0.1)',
            'acctstarttime': datetime(2023, 1, 1, 12, 0, 0),
            'acctstoptime': '2023-01-01 12:30:00',
            'acctsessiontime': '30m',
            'acctterminatecause': 'User-Request',
            'acctinputoctets': '130.445 KB',
            'acctoutputoctets': '357.501 KB',
        }

        if custom_attributes:
            default_attributes.update(custom_attributes)

        for attr, value in default_attributes.items():
            setattr(mock_result, attr, value)

        mock_query = MagicMock()
        mock_query.result = [mock_result]

        return mock_query

    return _create_mock


@pytest.fixture
def mock_log_detail_query():
    """Factory fixture for creating mocked LogDetailQuery"""

    def _create_mock(custom_attributes=None):
        mock_result = MagicMock()

        default_attributes = {
            'id': 12345,
            'username': 'test_user',
            'time': datetime(2023, 1, 1, 12, 0, 0),
            'type': 'Auth-Accept',
            'message': 'Login OK [user/test_realm]',
            'realm': 'test_realm',
        }

        if custom_attributes:
            default_attributes.update(custom_attributes)

        for attr, value in default_attributes.items():
            setattr(mock_result, attr, value)

        mock_query = MagicMock()
        mock_query.result = [mock_result]

        return mock_query

    return _create_mock
