from mock import Mock

import pytest

from nav.enterprise.ids import VENDOR_ID_HEWLETT_PACKARD, VENDOR_ID_CISCOSYSTEMS
from nav.models.manage import ManagementProfile
from nav.portadmin.management import ManagementFactory


@pytest.fixture
def profile():
    profile = ManagementProfile(
        protocol=ManagementProfile.PROTOCOL_SNMP,
        configuration={"version": 2, "community": "public"},
    )
    return profile


@pytest.fixture
def netbox_hp(profile):
    vendor = Mock()
    vendor.id = 'hp'

    netbox_type = Mock()
    netbox_type.vendor = vendor
    netbox_type.sysobjectid = '1.3.6.1.4.1.11.2.3.7.11.45'
    netbox_type.get_enterprise_id.return_value = VENDOR_ID_HEWLETT_PACKARD

    netbox = Mock()
    netbox.type = netbox_type
    netbox.ip = '10.240.160.39'
    netbox.get_preferred_snmp_management_profile.return_value = profile

    return netbox


@pytest.fixture
def netbox_cisco(profile):
    vendor = Mock()
    vendor.id = 'cisco'

    netbox_type = Mock()
    netbox_type.vendor = vendor
    netbox_type.sysobjectid = '1.3.6.1.4.1.9.1.278'
    netbox_type.get_enterprise_id.return_value = VENDOR_ID_CISCOSYSTEMS

    netbox = Mock()
    netbox.type = netbox_type
    netbox.ip = '10.240.160.38'
    netbox.get_preferred_snmp_management_profile.return_value = profile

    return netbox


@pytest.fixture
def netbox_cisco_smb(netbox_cisco):
    netbox_cisco.type.sysobjectid = '1.3.6.1.4.1.9.6.1.1004.10.1'
    return netbox_cisco


@pytest.fixture
def handler_hp(netbox_hp):
    return ManagementFactory.get_instance(netbox_hp)


@pytest.fixture
def handler_cisco(netbox_cisco):
    return ManagementFactory.get_instance(netbox_cisco)
