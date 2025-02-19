from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.arnold import QuarantineVlan


def test_arnold_manualdetention_should_not_crash(client):
    url = reverse('arnold-manual-detention')

    response = client.post(
        url,
        follow=True,
        data={
            'submit': 'Find',
            'target': '10.0.0.1',
        },  # any address will do
    )

    assert response.status_code == 200


def test_arnold_quarantine_vlan_twice_should_show_error_message(client):
    url = reverse('arnold-quarantinevlans')

    vlan_id = 1
    QuarantineVlan.objects.create(vlan=vlan_id, description='')

    response = client.post(
        url,
        follow=True,
        data={
            'vlan': vlan_id,
            'description': '',
            'qid': '',
            'submit': 'Add+vlan',
        },
    )

    assert response.status_code == 200
    assert "This vlan is already quarantined." in smart_str(response.content)
