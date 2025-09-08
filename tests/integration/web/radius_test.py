from urllib.parse import urlencode

from django.urls import reverse
from django.utils.encoding import smart_str


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
