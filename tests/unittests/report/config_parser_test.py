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
"""Tests for how the report name is matched against the configuration"""

import pytest

from nav.report.generator import ConfigParser


class TestParseReport:
    def test_when_name_matches_a_block_then_it_should_return_true(self, parser):
        assert parser.parse_report("room") is True

    def test_when_name_differs_only_in_case_then_it_should_return_true(self, parser):
        assert parser.parse_report("ROOM") is True

    def test_when_name_has_regex_metacharacters_then_it_should_match_literally(
        self, parser
    ):
        assert parser.parse_report("cam+arp") is True

    def test_when_name_is_a_pattern_matching_a_block_then_it_should_return_false(
        self, parser
    ):
        assert parser.parse_report("ro.m") is False

    def test_when_name_is_an_alternation_then_it_should_return_false(self, parser):
        assert parser.parse_report("room|netbox") is False

    def test_when_name_has_invalid_regex_syntax_then_it_should_return_false(
        self, parser
    ):
        assert parser.parse_report("(") is False


@pytest.fixture
def parser(tmp_path):
    config = tmp_path / "report.conf"
    config.write_text(
        'room {\n$sql="SELECT 1";\n}\n\ncam+arp {\n$sql="SELECT 2";\n}\n',
        encoding="utf-8",
    )
    return ConfigParser([str(config)])
