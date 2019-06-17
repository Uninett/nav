from __future__ import print_function

from django.urls import reverse
from django.http import Http404
from django.test.client import RequestFactory
from mock import MagicMock

from nav.models.manage import Netbox, Room
from nav.models.profiles import Account, AlertProfile
from nav.web.seeddb.page.netbox.edit import netbox_edit
from nav.web.seeddb.utils.delete import dependencies

import pytest


def test_usage_edit_url_should_allow_slashes():
    assert reverse('seeddb-usage-edit', args=('TEST/SLASH',))


def test_editing_deleted_netboxes_should_raise_404():
    netboxid = 666  # Assuming no such netbox exists in test data set!
    factory = RequestFactory()
    url = reverse('seeddb-netbox-edit', args=(netboxid,))
    request = factory.get(url)
    request.account = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
    request.session = MagicMock()

    with pytest.raises(Http404):
        netbox_edit(request, netboxid)


@pytest.fixture()
def netbox(management_profile):
    box = Netbox(ip='10.254.254.254', sysname='downhost.example.org',
                 organization_id='myorg', room_id='myroom', category_id='SRV')
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

