#
# Copyright (C) 2026 Uninett AS
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
"""Integration tests for report queries migrated onto Django's DB connection.

get_subnets() (IPtree) and MetaIP._createMetaMap() (metaIP) now run their raw
SQL through django.db.connection. These tests exercise that real cursor path.
"""

from IPy import IP as IPyIP

from nav.ip import IP
from nav.report.IPtree import get_subnets
from nav.report.metaIP import MetaIP


class TestGetSubnets:
    def test_when_queried_then_it_should_return_ip_objects_from_db(self, db):
        result = get_subnets(IP("10.0.0.0/8"))

        # Exercises the migrated django.db.connection cursor path; the result
        # depends on seeded data, so assert on shape rather than exact contents.
        assert isinstance(result, list)
        assert all(isinstance(net, IP) for net in result)
        assert all(net in IP("10.0.0.0/8") for net in result)


class TestMetaIP:
    def test_when_no_prefixes_exist_then_tree_net_should_still_render(self, db):
        MetaIP.invalidateCache()

        meta = MetaIP(IPyIP("10.0.0.0/24"))

        # No prefix data seeded, so no metadata is attached, but the migrated
        # query must run and getTreeNet() must produce the tree label.
        assert meta.prefixid is None
        assert meta.getTreeNet() == "10.0.0"
