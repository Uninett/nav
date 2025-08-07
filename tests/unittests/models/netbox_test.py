from unittest.mock import patch

from nav.models.manage import Netbox, ManagementProfile

import pytest


class TestGetPreferredSnmpProfiles:
    def test_when_write_required_is_false_then_it_should_prefer_a_read_profile(
        self, mocked_netbox
    ):
        profile = mocked_netbox.get_preferred_snmp_management_profile()
        assert profile.name == "v2 read"

    def test_when_write_required_is_true_then_it_should_return_a_write_profile(
        self, mocked_netbox
    ):
        profile = mocked_netbox.get_preferred_snmp_management_profile(
            require_write=True
        )
        assert profile.name.startswith("v2 write")

    def test_when_write_required_is_false_it_should_return_a_writable_profile_of_a_higher_snmp_version(  # noqa: E501
        self, mocked_netbox
    ):
        profiles = mocked_netbox.profiles.filter()
        profiles.append(
            ManagementProfile(
                name="v3 write",
                protocol=ManagementProfile.PROTOCOL_SNMPV3,
                configuration={"write": True},
            )
        )
        profile = mocked_netbox.get_preferred_snmp_management_profile()
        assert profile.name == "v3 write"


@pytest.fixture
def mocked_netbox(mock_profiles):
    with patch.object(Netbox, "profiles") as profiles:
        netbox = Netbox(sysname="test", ip="127.0.0.1")
        profiles.filter.return_value = mock_profiles
        yield netbox


@pytest.fixture
def mock_profiles():
    profiles = [
        ManagementProfile(
            name="v2 write first",
            protocol=ManagementProfile.PROTOCOL_SNMP,
            configuration={"version": 2, "write": True},
        ),
        ManagementProfile(
            name="v2 write second",
            protocol=ManagementProfile.PROTOCOL_SNMP,
            configuration={"version": 2, "write": True},
        ),
        ManagementProfile(
            name="v2 read",
            protocol=ManagementProfile.PROTOCOL_SNMP,
            configuration={"version": 2, "write": False},
        ),
    ]
    yield profiles
