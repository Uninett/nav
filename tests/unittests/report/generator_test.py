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

from nav.report.generator import (
    ArgumentParser,
    ReportConfig,
    _split_descending,
    _verbatim_sort_term,
)


class TestSplitDescending:
    def test_when_token_is_plain_then_it_should_be_ascending(self):
        assert _split_descending("sysname") == (False, "sysname")

    def test_when_token_has_leading_dash_then_it_should_be_descending(self):
        assert _split_descending("-sysname") == (True, "sysname")

    def test_when_token_has_an_inner_dash_then_it_should_keep_the_dash_in_the_name(
        self,
    ):
        assert _split_descending("a-b") == (False, "a-b")

    def test_when_descending_token_has_an_inner_dash_then_it_should_keep_the_inner_dash(  # noqa: E501
        self,
    ):
        assert _split_descending("-a-b") == (True, "a-b")


class TestVerbatimSortTerm:
    def test_when_token_is_ascending_then_it_should_be_emitted_verbatim(self):
        assert _verbatim_sort_term("priority") == "priority"

    def test_when_token_is_descending_then_it_should_get_a_desc_suffix(self):
        assert _verbatim_sort_term("-priority") == "priority DESC"

    def test_when_token_is_an_expression_then_it_should_not_be_quoted(self):
        assert _verbatim_sort_term("count(*)") == "count(*)"


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


class TestSortTokenNormalisation:
    def test_when_sort_tokens_have_whitespace_then_order_by_should_strip_them(self):
        config = ReportConfig()
        ArgumentParser(config).parse_query({"order_by": "sysname, ifindex"})
        assert config.order_by == ["sysname", "ifindex"]

    def test_when_a_sort_token_is_empty_then_order_by_should_drop_it(self):
        config = ReportConfig()
        ArgumentParser(config).parse_query({"order_by": "sysname,"})
        assert config.order_by == ["sysname"]
