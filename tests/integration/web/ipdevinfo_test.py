from __future__ import print_function

from django.urls import reverse
from django.utils.encoding import smart_text

from nav.models.manage import Netbox, Module, Interface, Device, NetboxProfile
from nav.web.ipdevinfo.utils import get_module_view

import pytest


def test_device_details_should_include_sysname(client, netbox):
    url = reverse('ipdevinfo-details-by-name', args=(netbox.sysname,))
    response = client.get(url)
    assert netbox.sysname in smart_text(response.content)


def test_port_search_should_match_case_insensitively(client, netbox):
    ifc = netbox.interface_set.all()[0]
    url = reverse('ipdevinfo-interface-details-by-name', kwargs={
        'netbox_sysname': netbox.sysname,
        'port_name': ifc.ifdescr.upper(),
    })
    response = client.get(url)
    assert response.status_code == 200
    assert ifc.ifdescr in smart_text(response.content)


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
def netbox(db, management_profile):
    box = Netbox(ip='10.254.254.254', sysname='example-sw.example.org',
                 organization_id='myorg', room_id='myroom', category_id='SW')
    box.save()
    NetboxProfile(netbox=box, profile=management_profile).save()

    device = Device(serial="1234test")
    device.save()
    module = Module(device=device, netbox=box, name='Module 1', model='')
    module.save()

    interface = Interface(netbox=box, module=module, ifname='1',
                          ifdescr='Port 1')
    interface.save()

    return box
