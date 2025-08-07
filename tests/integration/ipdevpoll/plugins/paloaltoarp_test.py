from unittest.mock import Mock

from django.urls import reverse
import pytest
import pytest_twisted
from twisted.internet import defer

from nav.models.manage import ManagementProfile, Netbox, NetboxProfile
from nav.ipdevpoll.jobs import JobHandler
from nav.ipdevpoll.plugins.paloaltoarp import PaloaltoArp
from nav.ipdevpoll.plugins import plugin_registry


class TestCanHandleNetbox:
    """
    Check that the PaloaltoArp plugin signifies it can handle netboxes with at
    least one management profile containing a paloalto configuration.
    """

    @pytest.mark.parametrize(
        "netbox",
        ["paloalto_netbox_1234", "paloalto_netbox_5678"],
    )
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_it_should_accept_netbox_having_some_paloalto_http_api_management_profile(
        self, netbox, request
    ):
        netbox = request.getfixturevalue(netbox)

        can_handle = yield PaloaltoArp.can_handle(netbox)
        assert can_handle

    @pytest.mark.parametrize(
        "netbox",
        ["no_paloalto_http_api_netbox", "no_http_api_netbox"],
    )
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_it_should_not_accept_netbox_without_any_paloalto_http_api_management_profile(  # noqa: E501
        self, netbox, request
    ):
        netbox = request.getfixturevalue(netbox)

        can_handle = yield PaloaltoArp.can_handle(netbox)
        assert not can_handle


class TestGetArpMappings:
    """
    Run the PaloaltoArp plugin on disparate pre-configured netboxes, then check
    that the expected arp mappings are assigned afterwards.
    """

    @pytest.mark.parametrize(
        "netbox",
        ["paloalto_netbox_1234"],
    )
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_it_should_get_arp_mappings_of_netbox_having_some_paloalto_management_profile_with_valid_api_key(  # noqa: E501
        self, netbox, monkeypatch, request
    ):
        netbox = request.getfixturevalue(netbox)

        # Set up a single ipdevpoll job for this netbox:
        # Assure PaloAltoArp is a known ipdevpoll plugin
        plugin_registry['paloaltoarp'] = PaloaltoArp
        job = JobHandler('paloaltoarp', netbox.pk, plugins=['paloaltoarp'])
        # Disable implicit SNMP requests done during job.run()
        job._create_agentproxy = Mock()
        job._destroy_agentproxy = Mock()

        monkeypatch.setattr(PaloaltoArp, "_do_request", _only_accept_1234)

        assert netbox.arp_set.count() == 0

        yield job.run()

        actual = [(arp.ip, arp.mac) for arp in netbox.arp_set.all()]
        expected = [
            ('192.168.0.1', '00:00:00:00:00:01'),
            ('192.168.0.2', '00:00:00:00:00:02'),
            ('192.168.0.3', '00:00:00:00:00:03'),
        ]
        assert sorted(actual) == sorted(expected)

    @pytest.mark.parametrize(
        "netbox",
        ["paloalto_netbox_5678", "no_paloalto_http_api_netbox", "no_http_api_netbox"],
    )
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_it_should_not_get_arp_mappings_of_netbox_without_any_paloalto_http_api_management_profile_with_valid_api_key(  # noqa: E501
        self, netbox, monkeypatch, request
    ):
        netbox = request.getfixturevalue(netbox)

        plugin_registry['paloaltoarp'] = PaloaltoArp
        job = JobHandler('paloaltoarp', netbox.pk, plugins=['paloaltoarp'])
        job._create_agentproxy = Mock()
        job._destroy_agentproxy = Mock()

        monkeypatch.setattr(PaloaltoArp, "_do_request", _only_accept_1234)

        assert netbox.arp_set.count() == 0
        yield job.run()
        assert netbox.arp_set.count() == 0


class TestEndToEnd:
    """Tests that mimic actual usage of the plugin"""

    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_it_should_get_arp_mappings_of_netbox_configured_with_paloalto_management_profile_using_seeddb(  # noqa: E501
        self, client, no_http_api_netbox, blank_management_profile, monkeypatch
    ):
        """
        Manually configure a netbox for use with the PaloaltoArp plugin, using
        SeedDB. Then run the PaloaltoArp plugin on this netbox and check that the
        expected arp mappings are assigned afterwards.
        """

        # Using SeedDB, edit a blank profile so that it now configures access to Palo
        # Alto ARP
        profile = blank_management_profile
        management_profile_url = reverse(
            "seeddb-management-profile-edit", args=(profile.id,)
        )
        client.post(
            management_profile_url,
            follow=True,
            data={
                "name": profile.name,
                "description": "",
                "protocol": ManagementProfile.PROTOCOL_HTTP_API,
                "service": "Palo Alto ARP",
                "api_key": "1234",
            },
        )

        # Using SeedDB, add the profile to a netbox with no prior Palo Alto ARP
        # management profile
        netbox = no_http_api_netbox
        netbox_url = reverse("seeddb-netbox-edit", args=(netbox.id,))
        client.post(
            netbox_url,
            follow=True,
            data={
                "ip": netbox.ip,
                "room": netbox.room_id,
                "category": netbox.category_id,
                "organization": netbox.organization_id,
                "profiles": [profile.id],
            },
        )
        profile.refresh_from_db()
        netbox.refresh_from_db()

        # Now check that the plugin correctly fetches arp mappings from this netbox
        plugin_registry['paloaltoarp'] = PaloaltoArp
        job = JobHandler('paloaltoarp', netbox.pk, plugins=['paloaltoarp'])

        job._create_agentproxy = Mock()
        job._destroy_agentproxy = Mock()

        monkeypatch.setattr(PaloaltoArp, "_do_request", _only_accept_1234)

        assert netbox.arp_set.count() == 0

        yield job.run()

        actual = [(arp.ip, arp.mac) for arp in netbox.arp_set.all()]
        expected = [
            ('192.168.0.1', '00:00:00:00:00:01'),
            ('192.168.0.2', '00:00:00:00:00:02'),
            ('192.168.0.3', '00:00:00:00:00:03'),
        ]
        assert sorted(actual) == sorted(expected)


valid_http_response_body = b'''
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


def _only_accept_1234(self, address, key, *args, **kwargs):
    """Mimic PaloaltoArp._do_request() but only succeed if supplied key is '1234'"""
    if key == "1234":
        return defer.succeed(valid_http_response_body)
    return defer.succeed(None)


@pytest.fixture
def paloalto_netbox_1234():
    """
    Netbox with a PaloAlto HTTP
    """
    netbox = Netbox(
        ip="10.0.0.1",
        sysname="fw1.example.org",
        organization_id="myorg",
        room_id="myroom",
        category_id="SRV",
    )
    netbox.save()

    profile = ManagementProfile(
        name="PaloAlto Profile 1",
        protocol=ManagementProfile.PROTOCOL_HTTP_API,
        configuration={
            "api_key": "1234",
            "service": "Palo Alto ARP",
        },
    )
    profile.save()
    NetboxProfile(netbox=netbox, profile=profile).save()

    yield netbox
    netbox.delete()
    profile.delete()


@pytest.fixture
def paloalto_netbox_5678():
    netbox = Netbox(
        ip="10.0.0.2",
        sysname="fw2.example.org",
        organization_id="myorg",
        room_id="myroom",
        category_id="SRV",
    )
    netbox.save()

    profile = ManagementProfile(
        name="PaloAlto Profile 2",
        protocol=ManagementProfile.PROTOCOL_HTTP_API,
        configuration={
            "api_key": "5678",
            "service": "Palo Alto ARP",
        },
    )
    profile.save()
    NetboxProfile(netbox=netbox, profile=profile).save()

    yield netbox
    netbox.delete()
    profile.delete()


@pytest.fixture
def no_http_api_netbox():
    netbox = Netbox(
        ip="10.0.0.3",
        sysname="gw1.example.org",
        organization_id="myorg",
        room_id="myroom",
        category_id="GW",
    )
    netbox.save()

    profile = ManagementProfile(
        name="SNMP v1 write profile",
        protocol=ManagementProfile.PROTOCOL_SNMP,
        configuration={
            "community": "secret",
            "version": 1,
            "write": True,
            "api_key": "1234",
            "service": "Palo Alto ARP",
        },
    )
    profile.save()
    NetboxProfile(netbox=netbox, profile=profile).save()

    yield netbox
    netbox.delete()
    profile.delete()


@pytest.fixture
def no_paloalto_http_api_netbox():
    netbox = Netbox(
        ip="10.0.0.4",
        sysname="dns.example.org",
        organization_id="myorg",
        room_id="myroom",
        category_id="SRV",
    )
    netbox.save()

    profile = ManagementProfile(
        name="PaloAlto Test Management Profile",
        protocol=ManagementProfile.PROTOCOL_HTTP_API,
        configuration={
            "api_key": "1234",
            "service": "DNS",
        },
    )
    profile.save()
    NetboxProfile(netbox=netbox, profile=profile).save()

    yield netbox
    netbox.delete()
    profile.delete()


@pytest.fixture
def blank_management_profile():
    profile = ManagementProfile(
        name="Manually Configured Paloaltoarp Profile",
        protocol=ManagementProfile.PROTOCOL_DEBUG,
        configuration={},
    )
    profile.save()
    yield profile
    profile.delete()
