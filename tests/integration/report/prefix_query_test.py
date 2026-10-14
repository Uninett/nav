#
# Copyright (C) 2026 University of Oslo
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
"""Integration tests for report prefix queries on Django's DB connection.

get_subnets() (IPtree) and MetaIP._createMetaMap() (metaIP) now run their raw
SQL through django.db.connection, which is the same connection the test
transaction runs on. That is what lets these tests see the prefix seeded below;
against the old nav.db.getConnection() path, a separate connection, the
uncommitted row would be invisible and these assertions would fail.
"""

import pytest

from IPy import IP as IPyIP

from nav.ip import IP
from nav.models.manage import Prefix, Vlan
from nav.report.IPtree import get_subnets
from nav.report.metaIP import MetaIP


class TestGetSubnets:
    def test_when_queried_then_it_should_return_seeded_subnet_from_db(
        self, seeded_prefix
    ):
        result = get_subnets(IP("10.0.0.0/8"))

        assert IP("10.0.0.0/24") in result
        assert all(isinstance(net, IP) for net in result)


class TestMetaIP:
    def test_when_prefix_exists_then_it_should_attach_metadata(self, seeded_prefix):
        meta = MetaIP(IPyIP("10.0.0.0/24"))

        assert meta.prefixid == seeded_prefix.id
        assert meta.nettype == "lan"
        assert meta.getTreeNet() == "10.0.0"


@pytest.fixture
def seeded_prefix(db):
    vlan = Vlan.objects.create(vlan=10, net_type_id="lan")
    return Prefix.objects.create(net_address="10.0.0.0/24", vlan=vlan)


@pytest.fixture(autouse=True)
def _clear_metaip_cache():
    # MetaMap is a class-level cache built inside the rolled-back test
    # transaction; clear it both ways so it never leaks between tests.
    MetaIP.invalidateCache()
    yield
    MetaIP.invalidateCache()
