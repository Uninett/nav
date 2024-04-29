#
# Copyright (C) 2023 Sikt
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
from unittest.mock import Mock

import pytest

from nav.Snmp import Snmp
from nav.Snmp.profile import get_snmp_session_for_profile


class TestGetSnmpSessionForProfile:
    def test_when_valid_snmpv2_profile_is_given_it_should_return_a_valid_snmp_partial(
        self, mock_snmpv2_profile
    ):
        snmp = get_snmp_session_for_profile(mock_snmpv2_profile)
        assert callable(snmp)
        session = snmp("127.0.0.1")
        assert isinstance(session, Snmp)

    def test_when_valid_snmpv3_profile_is_given_it_should_return_a_valid_snmp_partial(
        self, mock_snmpv3_profile
    ):
        snmp = get_snmp_session_for_profile(mock_snmpv3_profile)
        assert callable(snmp)
        session = snmp("127.0.0.1")
        assert isinstance(session, Snmp)

        conf = mock_snmpv3_profile.configuration
        assert session.sec_level.value == conf["sec_level"]
        assert session.auth_protocol.value == conf["auth_protocol"]
        assert session.sec_name == conf["sec_name"]
        assert session.auth_password == conf["auth_password"]

    def test_when_non_snmp_profile_is_given_it_should_raise_valueerror(self):
        profile = Mock(is_snmp=False)
        with pytest.raises(ValueError):
            get_snmp_session_for_profile(profile)


@pytest.fixture
def mock_snmpv2_profile():
    profile = Mock(is_snmp=True, snmp_version=2)
    profile.configuration = {
        "version": "2c",
        "write": False,
        "community": "public",
    }
    return profile


@pytest.fixture
def mock_snmpv3_profile():
    profile = Mock(is_snmp=True, snmp_version=3)
    profile.configuration = {
        "version": "3",
        "sec_level": "authNoPriv",
        "auth_protocol": "SHA",
        "sec_name": "foobar",
        "auth_password": "zaphodbeeblebrox",
    }
    return profile
