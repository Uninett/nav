#
# Copyright (C) 2022 Sikt
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
import pytest_twisted

from nav.ipdevpoll.utils import get_arista_vrf_instances


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_get_arista_vrf_instances_should_return_expected_instances(snmp_agent_proxy):
    snmp_agent_proxy.community = 'arista'
    snmp_agent_proxy.open()

    result = yield get_arista_vrf_instances(snmp_agent_proxy)
    expected = [
        ('', 'arista'),
        ('IOT', 'arista@IOT'),
        ('MGMT', 'arista@MGMT'),
        ('STUDENT', 'arista@STUDENT'),
        ('VR', 'arista@VR'),
    ]
    assert set(result) == set(expected)
