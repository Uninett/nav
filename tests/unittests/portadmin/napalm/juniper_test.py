#
# Copyright (C) 2022 Sikt AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

import napalm
import pytest
from unittest.mock import Mock, patch

from jnpr.junos.exception import RpcError

from nav.enterprise.ids import VENDOR_ID_RESERVED, VENDOR_ID_JUNIPER_NETWORKS_INC
from nav.models import manage
from nav.portadmin.handlers import DeviceNotConfigurableError, ProtocolError
from nav.portadmin.napalm.juniper import wrap_unhandled_rpc_errors, Juniper


@pytest.fixture()
def netbox_mock():
    """Create netbox model mock object"""
    netbox = Mock()
    netbox.ip = '10.0.0.1'
    netbox.type.get_enterprise_id.return_value = VENDOR_ID_JUNIPER_NETWORKS_INC
    yield netbox


@pytest.fixture()
def profile_mock():
    """Create management profile model mock object"""
    profile = Mock()
    profile.protocol = manage.ManagementProfile.PROTOCOL_NAPALM
    profile.PROTOCOL_NAPALM = manage.ManagementProfile.PROTOCOL_NAPALM
    profile.configuration = {"driver": "mock"}
    yield profile


class TestWrapUnhandledRpcErrors:
    def test_rpcerrors_should_become_protocolerrors(self):
        @wrap_unhandled_rpc_errors
        def wrapped_function():
            raise RpcError("bogus")

        with pytest.raises(ProtocolError):
            wrapped_function()

    def test_non_rpcerrors_should_pass_through(self):
        @wrap_unhandled_rpc_errors
        def wrapped_function():
            raise TypeError("bogus")

        with pytest.raises(TypeError):
            wrapped_function()


class TestJuniper:
    def test_juniper_device_returns_device_connection(self, netbox_mock, profile_mock):
        driver = napalm.get_network_driver('mock')
        device = driver(
            hostname='foo',
            username='user',
            password='pass',
            optional_args={},
        )
        device.open()
        juniper = Juniper(netbox=netbox_mock)
        juniper._profile = profile_mock

        assert juniper.device

    def test_juniper_device_raises_error_if_vendor_not_juniper(
        self, netbox_mock, profile_mock
    ):
        netbox_mock.type.get_enterprise_id.return_value = VENDOR_ID_RESERVED
        juniper = Juniper(netbox=netbox_mock)
        juniper._profile = profile_mock

        with pytest.raises(DeviceNotConfigurableError):
            juniper.device

    def test_juniper_device_raises_error_if_no_connected_profile(self, netbox_mock):
        juniper = Juniper(netbox=netbox_mock)
        netbox_mock.profiles.filter.return_value.first.return_value = None

        with pytest.raises(DeviceNotConfigurableError):
            juniper.device

    @patch('nav.models.manage.Vlan.objects', Mock(return_value=[]))
    def test_get_netbox_vlans_should_ignore_vlans_with_non_integer_tags(self):
        """Regression test for #2452"""

        class MockedJuniperHandler(Juniper):
            @property
            def vlans(self):
                """Mock a VLAN table response from the device"""
                return [Mock(tag='NA'), Mock(tag='10')]

        m = MockedJuniperHandler(Mock())
        assert len(m.get_netbox_vlans()) == 1
