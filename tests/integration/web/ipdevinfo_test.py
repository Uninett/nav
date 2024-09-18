# -*- coding: utf-8 -*-

from django.urls import reverse
from django.utils.encoding import smart_str

from nav.models.manage import Netbox, Module, Interface, Device, NetboxProfile
from nav.web.ipdevinfo.utils import get_module_view

import pytest


def test_device_details_should_include_sysname(client, netbox):
    url = reverse('ipdevinfo-details-by-name', args=(netbox.sysname,))
    response = client.get(url)
    assert netbox.sysname in smart_str(response.content)


def test_port_search_should_match_case_insensitively(client, netbox):
    ifc = netbox.interfaces.all()[0]
    url = reverse(
        'ipdevinfo-interface-details-by-name',
        kwargs={
            'netbox_sysname': netbox.sysname,
            'port_name': ifc.ifdescr.upper(),
        },
    )
    response = client.get(url)
    assert response.status_code == 200
    assert ifc.ifdescr in smart_str(response.content)


@pytest.mark.parametrize(
    "perspective",
    [
        'swportstatus',
        'swportactive',
        'gwportstatus',
        'physportstatus',
    ],
)
def test_get_module_view(netbox, perspective):
    module = netbox.modules.all()[0]
    result = get_module_view(module, perspective='swportstatus', netbox=netbox)
    assert result['object'] == module
    assert 'ports' in result


@pytest.mark.parametrize(
    "badname",
    [
        "02.44.02",  # Looks like an IP address
        u"\x01\x9e$ü\x86",  # Cannot be encoded using IDNA for DNS lookups
    ],
)
def test_bad_name_should_not_crash_ipdevinfo(client, badname):
    """Tests "bad" device names to ensure they dont crash ipdevinfo lookup views"""
    url = reverse("ipdevinfo-details-by-name", kwargs={"name": badname})
    response = client.get(url)
    assert response.status_code == 200
    assert badname in smart_str(response.content)


###
#
# Fixtures
#
###


@pytest.fixture()
def netbox(db, management_profile):
    box = Netbox(
        ip='10.254.254.254',
        sysname='example-sw.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SW',
    )
    box.save()
    NetboxProfile(netbox=box, profile=management_profile).save()

    device = Device(serial="1234test")
    device.save()
    module = Module(device=device, netbox=box, name='Module 1', model='')
    module.save()

    interface = Interface(netbox=box, module=module, ifname='1', ifdescr='Port 1')
    interface.save()

    return box
