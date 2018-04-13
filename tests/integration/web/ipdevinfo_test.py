from __future__ import print_function

from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from mock import MagicMock

from nav.models.manage import Netbox
from nav.models.profiles import Account

from nav.web.ipdevinfo.views import ipdev_details

import pytest


def test_device_details_should_include_sysname(netbox):
    factory = RequestFactory()
    url = reverse('ipdevinfo-details-by-name', args=(netbox.sysname,))
    request = factory.get(url)
    request.account = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
    request.session = MagicMock()

    response = ipdev_details(request, name=netbox.sysname)
    assert netbox.sysname in response.content


###
#
# Fixtures
#
###

@pytest.fixture()
def netbox():
    box = Netbox(ip='10.254.254.254', sysname='example-srv.example.org',
                 organization_id='myorg', room_id='myroom', category_id='SRV',
                 snmp_version=2)
    box.save()
    yield box
    print("teardown test device")
    box.delete()
