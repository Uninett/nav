import pytest
from unittest.mock import Mock

from nav.enterprise.ids import VENDOR_ID_JUNIPER_NETWORKS_INC
from nav.models import manage
from nav.portadmin.napalm.juniper import Juniper


@pytest.fixture()
def netbox_mock(interface1_mock, interface2_mock):
    """Create netbox model mock object"""
    netbox = Mock()
    netbox.ip = '10.0.0.1'
    netbox.type.get_enterprise_id.return_value = VENDOR_ID_JUNIPER_NETWORKS_INC
    netbox.interfaces = [interface1_mock, interface2_mock]
    yield netbox


@pytest.fixture()
def profile_mock():
    """Create management profile model mock object"""
    profile = Mock()
    profile.protocol = manage.ManagementProfile.PROTOCOL_NAPALM
    profile.PROTOCOL_NAPALM = manage.ManagementProfile.PROTOCOL_NAPALM
    profile.configuration = {"driver": "mock"}
    yield profile


@pytest.fixture()
def handler_mock(netbox_mock, profile_mock):
    """Create management handler mock object"""
    juniper = Juniper(netbox=netbox_mock)
    juniper._profile = profile_mock
    yield juniper


@pytest.fixture()
def interface1_mock():
    interface = Mock()
    interface.ifname = "ge-0/0/1"
    interface.ifindex = 1
    yield interface


@pytest.fixture()
def interface2_mock():
    interface = Mock()
    interface.ifname = "ge-0/0/2"
    interface.ifindex = 2
    yield interface
