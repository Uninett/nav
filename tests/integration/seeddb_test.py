from __future__ import print_function

from django.urls import reverse
from django.http import Http404
from django.test.client import RequestFactory
from mock import MagicMock

from django.utils.encoding import smart_str
from nav.models.manage import Netbox, Room
from nav.web.seeddb.page.netbox.edit import netbox_edit, log_netbox_change
from nav.web.seeddb.utils.delete import dependencies

import pytest


def test_usage_edit_url_should_allow_slashes():
    assert reverse('seeddb-usage-edit', args=('TEST/SLASH',))


def test_editing_deleted_netboxes_should_raise_404(admin_account):
    netboxid = 666  # Assuming no such netbox exists in test data set!
    factory = RequestFactory()
    url = reverse('seeddb-netbox-edit', args=(netboxid,))
    request = factory.get(url)
    request.account = admin_account
    request.session = MagicMock()

    with pytest.raises(Http404):
        netbox_edit(request, netboxid)


def test_adding_netbox_with_invalid_ip_should_fail(db, client):
    url = reverse('seeddb-netbox-edit')
    ip = "195.88.54.16'))) OR 2121=(SELECT COUNT(*) FROM GENERATE_SERIES(1,15000000)) AND ((('FRyc' LIKE 'FRyc"

    response = client.post(
        url,
        follow=True,
        data={
            "ip": ip,
            "room": "myroom",
            "category": "GW",
            "organization": "myorg",
        },
    )

    assert response.status_code == 200
    assert 'Form was not valid' in smart_str(response.content)
    assert 'Could not resolve name' in smart_str(response.content)


def test_adding_netbox_with_invalid_profiles_should_fail(db, client):
    url = reverse('seeddb-netbox-edit')
    ip = "10.254.254.253"

    response = client.post(
        url,
        follow=True,
        data={
            "ip": ip,
            "room": "myroom",
            "category": "GW",
            "organization": "myorg",
            "profiles": "-5785')) ORDER BY 1-- qAPu",
        },
    )

    assert response.status_code == 200
    assert 'Form was not valid' in smart_str(response.content)
    assert not Netbox.objects.filter(ip=ip).exists()


@pytest.fixture()
def netbox(management_profile):
    box = Netbox(
        ip='10.254.254.254',
        sysname='downhost.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SRV',
    )
    box.save()
    yield box
    print("teardown test device")
    box.delete()


def test_dependencies(netbox):
    """Tests the related objects listed when deleting objects in seeddb"""
    qs = Room.objects.filter(pk='myroom')
    deps = dependencies(qs, [Netbox])
    assert 'myroom' in deps
    assert [netbox] == deps.get('myroom')


def test_dependencies_no_whitelist(netbox):
    """Tests the related objects listed when deleting objects in seeddb"""
    qs = Room.objects.filter(pk='myroom')
    deps = dependencies(qs, [])
    assert Netbox.objects.get(pk=netbox.pk)
    assert deps == {}


def test_log_netbox_change_should_not_crash(admin_account, netbox):
    """Regression test to ensure this function doesn't try to access removed or
    invalid attributes on Netbox.
    """
    old = Netbox.objects.get(id=netbox.id)
    new = netbox
    new.category_id = "OTHER"

    assert log_netbox_change(admin_account, old, new) is None
