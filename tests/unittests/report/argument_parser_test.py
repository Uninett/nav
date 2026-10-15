#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Tests for which report settings a request's query arguments may change"""

import pytest

from nav.report.generator import ArgumentParser, ReportConfig


class TestParseQuery:
    @pytest.mark.parametrize("arg", ["uri_roomid", "url_roomid"])
    def test_when_query_has_a_link_then_it_should_ignore_it(self, arg):
        config = ReportConfig()
        config.uri["roomid"] = "/search/room/$roomid/"

        fields, _, _ = ArgumentParser(config).parse_query({arg: "javascript:x()"})

        assert config.uri == {"roomid": "/search/room/$roomid/"}
        assert fields == {}

    @pytest.mark.parametrize("arg", ["extra", "ekstra"])
    def test_when_query_has_an_extra_column_then_it_should_ignore_it(self, arg):
        config = ReportConfig()

        fields, _, _ = ArgumentParser(config).parse_query({arg: "sysname"})

        assert config.extra == []
        assert fields == {}
