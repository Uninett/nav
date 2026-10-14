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
"""Unit tests for the connection-free parts of the report generator."""

from nav.report.generator import ReportConfig, ArgumentParser


class TestOrderByProperty:
    def test_when_sort_comes_from_request_then_order_by_should_expose_plain_tokens(
        self,
    ):
        config = ReportConfig()
        ArgumentParser(config).parse_query({"order_by": "-sysname"})
        assert config.order_by == ["-sysname"]

    def test_when_request_and_config_sort_both_exist_then_order_by_should_list_request_tokens_first(  # noqa: E501
        self,
    ):
        config = ReportConfig()
        config.add_trusted_sort(["roomid"])
        ArgumentParser(config).parse_query({"order_by": "sysname"})
        assert config.order_by == ["sysname", "roomid"]
