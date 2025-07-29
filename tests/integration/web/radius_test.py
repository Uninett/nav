from django.urls import reverse
from django.utils.encoding import smart_str


def test_top_talkers_should_not_crash_on_big_days(db, client):
    url = reverse('radius-account_charts')
    url = (
        url + '?days=123123123123&charts=sentrecv&charts=recv&charts=sent&send=Show+me'
    )
    response = client.get(url)

    assert response.status_code == 200
    assert 'They did not have computers' in smart_str(response.content)


def test_account_log_search_should_not_crash_on_big_days(db, client, admin_username):
    url = reverse('radius-account_search')
    url = (
        url
        + f'?query_0=username&query_1={admin_username}&time_0=days'
        + '&time_1=123123123123123&port_type=&send=Search'
    )
    response = client.get(url)

    assert response.status_code == 200
    assert 'They did not have computers' in smart_str(response.content)


def test_error_log_search_should_not_crash_on_big_hours(db, client, admin_username):
    url = reverse('radius-log_search')
    url += (
        f'?query_0=username&query_1={admin_username}&log_entry_type=&time_0=hours'
        '&time_1=123123123123123&send=Search'
    )
    response = client.get(url)

    assert response.status_code == 200
    assert 'They did not have computers' in smart_str(response.content)
