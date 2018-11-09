from django.core.urlresolvers import reverse


def test_arnold_manualdetention_should_not_crash(client):
    url = reverse('arnold-manual-detention')

    response = client.post(url, follow=True, data={
        'submit': 'Find',
        'target': '10.0.0.1',  # any address will do
    })

    assert response.status_code == 200
