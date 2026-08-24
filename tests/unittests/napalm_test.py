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

import pytest
from unittest.mock import Mock

import napalm

from nav.models import manage
from nav.napalm import connect, NapalmError


@pytest.fixture()
def netbox_mock():
    """Create netbox model mock object"""
    netbox = Mock()
    netbox.ip = '10.0.0.1'
    return netbox


@pytest.fixture()
def profile_mock():
    """Create management profile model mock object"""
    profile = Mock()
    profile.protocol = manage.ManagementProfile.PROTOCOL_NAPALM
    profile.PROTOCOL_NAPALM = manage.ManagementProfile.PROTOCOL_NAPALM
    profile.configuration = {"driver": "mock"}
    return profile


class TestNapalm:
    def test_napalm_connect_runs_without_errors_for_correct_netbox_and_profile(
        self, netbox_mock, profile_mock
    ):
        device = connect(
            host=netbox_mock,
            profile=profile_mock,
        )

        assert device

    def test_napalm_connect_throws_exception_for_snmp_profile(
        self, netbox_mock, profile_mock
    ):
        profile_mock.protocol = manage.ManagementProfile.PROTOCOL_SNMP

        with pytest.raises(NapalmError):
            connect(host=netbox_mock, profile=profile_mock)

    def test_napalm_connect_throws_exception_for_profile_without_driver(
        self, netbox_mock, profile_mock
    ):
        profile_mock.configuration = {}
        with pytest.raises(NapalmError):
            connect(host=netbox_mock, profile=profile_mock)


def test_when_hostname_is_a_bare_ipv6_address_then_the_junos_driver_should_accept_it():
    """Regression test for #4119.

    junos-eznc 2.8.1 started rejecting unbracketed IPv6 literals as the host
    value, while napalm's junos driver hands them the device IP verbatim. NAV
    always hands bare IP addresses to the Napalm driver, so constructing the junos
    driver with one must not raise. Construction is where the driver builds the
    jnpr.junos.Device and PyEZ validates the host; no network I/O happens until
    open(), so this stays a pure unit test.
    """
    junos_driver = napalm.get_network_driver("junos")

    device = junos_driver(hostname="2001:db8::1", username="admin", password="x")

    assert device.hostname == "2001:db8::1"
