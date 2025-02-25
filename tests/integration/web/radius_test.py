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
