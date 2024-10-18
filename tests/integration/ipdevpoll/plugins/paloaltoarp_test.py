from unittest.mock import Mock

import pytest
import pytest_twisted
from twisted.internet import defer

from django.urls import reverse
from nav.models.manage import ManagementProfile, Netbox
from nav.ipdevpoll import shadows
from nav.ipdevpoll.jobs import JobHandler
from nav.ipdevpoll.plugins.paloaltoarp import PaloaltoArp
from nav.ipdevpoll.plugins import plugin_registry
from nav.ipdevpoll.storage import ContainerRepository
from IPy import IP


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_netbox_with_paloalto_management_profile_with_valid_api_key_should_get_arp_mappings(
    paloalto_netbox_1234, monkeypatch
):
    assert PaloaltoArp.can_handle(paloalto_netbox_1234)

    # Set up a single ipdevpoll job for this netbox:
    # Assure PaloAltoArp is a known ipdevpoll plugin
    plugin_registry['paloaltoarp'] = PaloaltoArp
    job = JobHandler('paloaltoarp', paloalto_netbox_1234.pk, plugins=['paloaltoarp'])
    # Disable implicit SNMP requests done during job.run()
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()

    monkeypatch.setattr(PaloaltoArp, "_do_request", _only_accept_netbox_1234)

    assert paloalto_netbox_1234.arp_set.count() == 0

    yield job.run()

    actual = [(arp.ip, arp.mac) for arp in paloalto_netbox_1234.arp_set.all()]
    expected = [
        (IP('192.168.0.1'), '00:00:00:00:00:01'),
        (IP('192.168.0.2'), '00:00:00:00:00:02'),
        (IP('192.168.0.3'), '00:00:00:00:00:03'),
    ]
    assert sorted(actual) == sorted(expected)


def test_netbox_with_paloalto_management_profile_with_invalid_api_key_should_not_get_arp_mappings(
    paloalto_netbox_1234, monkeypatch
):
    assert PaloaltoArp.can_handle(paloalto_netbox_1234)

    plugin_registry['paloaltoarp'] = PaloaltoArp
    job = JobHandler('paloaltoarp', paloalto_netbox_1234.pk, plugins=['paloaltoarp'])
    job._create_agentproxy = Mock()
    job._destroy_agentproxy = Mock()

    monkeypatch.setattr(PaloaltoArp, "_do_request", _only_accept_netbox_5678)

    assert paloalto_netbox_1234.arp_set.count() == 0
    yield job.run()
    assert paloalto_netbox_1234.arp_set.count() == 0


mock_data = b'''
    <response status="success">
    <result>
            <max>132000</max>
            <total>3</total>
            <timeout>1800</timeout>
            <dp>s3dp1</dp>
            <entries>
                <entry>
                    <status>  s  </status>
                    <ip>192.168.0.1</ip>
                    <mac>00:00:00:00:00:01</mac>
                    <ttl>100</ttl>
                    <interface>ae2</interface>
                    <port>ae2</port>
                </entry>
                <entry>
                    <status>  e  </status>
                    <ip>192.168.0.2</ip>
                    <mac>00:00:00:00:00:02</mac>
                    <ttl>200</ttl>
                    <interface>ae2</interface>
                    <port>ae2</port>
                </entry>
                <entry>
                    <status>  c  </status>
                    <ip>192.168.0.3</ip>
                    <mac>00:00:00:00:00:03</mac>
                    <ttl>300</ttl>
                    <interface>ae3.61</interface>
                    <port>ae3</port>
                </entry>
                <entry>
                    <status>  i  </status>
                    <ip>192.168.0.4</ip>
                    <mac>00:00:00:00:00:04</mac>
                    <ttl>400</ttl>
                    <interface>ae3.61</interface>
                    <port>ae3</port>
                </entry>
            </entries>
        </result>
    </response>
    '''


@pytest.fixture
def paloalto_netbox_1234(db, client):
    box = Netbox(
        ip='127.0.0.1',
        sysname='localhost.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SRV',
    )
    box.save()
    profile = ManagementProfile(
        name="PaloAlto Test Management Profile",
        protocol=ManagementProfile.PROTOCOL_SNMP,  # Correct protocol is set with HTTP POST below
        configuration={
            "version": 2,
            "community": "public",
            "write": False,
        },
    )
    profile.save()

    netbox_url = reverse("seeddb-netbox-edit", args=(box.id,))
    management_profile_url = reverse(
        "seeddb-management-profile-edit", args=(profile.id,)
    )

    # Manually sending this post request helps reveal regression bugs in case
    # HTTPRestForm.service.choices keys are altered; because the post's thus
    # invalid service field should then cause the django form cleaning stage to
    # fail. (Changing the HTTPRestForm.choice map to use enums as keys instead
    # of strings would enable static analysis to reveal this.)
    client.post(
        management_profile_url,
        follow=True,
        data={
            "name": profile.name,
            "description": profile.description,
            "protocol": ManagementProfile.PROTOCOL_HTTP_REST,
            "service": "Palo Alto ARP",
            "api_key": "1234",
        },
    )

    client.post(
        netbox_url,
        follow=True,
        data={
            "ip": box.ip,
            "room": box.room_id,
            "category": box.category_id,
            "organization": box.organization_id,
            "profiles": [profile.id],
        },
    )

    yield box
    print("teardown test device")
    box.delete()
    profile.delete()


@defer.inlineCallbacks
def _only_accept_netbox_1234(address, key, *args, **kwargs):
    if key == "1234":
        pytest_twisted.returnValue(mock_data)
    pytest_twisted.returnValue(None)


@defer.inlineCallbacks
def _only_accept_netbox_5678(address, key, *args, **kwargs):
    if key == "5678":
        pytest_twisted.returnValue(mock_data)
    pytest_twisted.returnValue(None)
