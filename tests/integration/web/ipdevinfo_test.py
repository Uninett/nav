from __future__ import print_function

from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from mock import MagicMock

from nav.models.manage import Netbox, Module, Interface, Device
from nav.models.profiles import Account

from nav.web.ipdevinfo.views import ipdev_details
from nav.web.ipdevinfo.utils import get_module_view

import pytest


def test_device_details_should_include_sysname(netbox):
    factory = RequestFactory()
    url = reverse('ipdevinfo-details-by-name', args=(netbox.sysname,))
    request = factory.get(url)
    request.account = Account.objects.get(pk=Account.ADMIN_ACCOUNT)
    request.session = MagicMock()

    response = ipdev_details(request, name=netbox.sysname)
    assert netbox.sysname in response.content


@pytest.mark.parametrize("perspective", [
    'swportstatus',
    'swportactive',
    'gwportstatus',
    'physportstatus',
])
def test_get_module_view(netbox, perspective):
    module = netbox.module_set.all()[0]
    result = get_module_view(module, perspective='swportstatus', netbox=netbox)
    assert result['object'] == module
    assert 'ports' in result

###
#
# Fixtures
#
###


@pytest.fixture()
def netbox():
    box = Netbox(ip='10.254.254.254', sysname='example-sw.example.org',
                 organization_id='myorg', room_id='myroom', category_id='SW',
                 snmp_version=2, read_only='public')
    box.save()

    device = Device(serial="1234test")
    device.save()
    module = Module(device=device, netbox=box, name='Module 1', model='')
    module.save()

    interface = Interface(netbox=box, module=module, ifname='1',
                          ifdescr='Port 1')
    interface.save()

    yield box
    print("teardown test device")
    box.delete()
    device.delete()
