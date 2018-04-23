from __future__ import print_function

from django.core.urlresolvers import reverse
from django.utils.encoding import smart_text

from nav.models.manage import Netbox, Module, Interface, Device
from nav.web.ipdevinfo.utils import get_module_view

import pytest


def test_device_details_should_include_sysname(client, netbox):
    url = reverse('ipdevinfo-details-by-name', args=(netbox.sysname,))
    response = client.get(url)
    assert netbox.sysname in smart_text(response.content)


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
def netbox(db):
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

    return box
