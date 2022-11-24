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

from nav.ip import IP
from nav.mibs.ip_mib import MultiIpMib
from nav.ipdevpoll.utils import get_arista_vrf_instances


class TestMultiIpMib:
    @pytest.mark.twisted
    @pytest_twisted.inlineCallbacks
    def test_get_ifindex_ip_mac_mappings_should_find_mappings_across_arista_vrfs(
        self, snmp_agent_proxy
    ):
        snmp_agent_proxy.community = 'arista'
        snmp_agent_proxy.open()
        instances = yield get_arista_vrf_instances(snmp_agent_proxy)
        mib = MultiIpMib(snmp_agent_proxy, instances=instances)

        result = yield mib.get_ifindex_ip_mac_mappings()
        # assert at least one from each VRF with a mapping (main, STUDENT and MGMT)
        assert (2000223, IP('fe80::a8aa:aaff:feaa:aaaa'), 'aa:aa:aa:aa:aa:aa') in result
        assert (40, IP('10.103.0.0'), 'f4:cc:55:44:3d:29') in result
        assert (50001, IP('10.101.1.12'), 'fc:bd:67:d0:fb:5d') in result
