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

import pytest

from nav.topology.stats import NullStats, ReducerStats


class TestReducerStatsCounters:
    def test_when_counter_is_incremented_then_it_should_accumulate(self):
        stats = ReducerStats()
        stats.lldp["pairs_matched"] += 1
        stats.lldp["pairs_matched"] += 1
        assert stats.lldp["pairs_matched"] == 2

    def test_when_counter_is_not_touched_then_it_should_default_to_zero(self):
        stats = ReducerStats()
        assert stats.cam["resolved_return_path"] == 0


class TestReducerStatsTimePhase:
    def test_when_phase_completes_then_duration_should_be_recorded(self):
        stats = ReducerStats()
        with stats.time_phase("load"):
            pass
        assert "load" in stats.phase_timings
        assert stats.phase_timings["load"] >= 0

    def test_when_phase_raises_then_duration_should_still_be_recorded(self):
        stats = ReducerStats()
        with pytest.raises(RuntimeError):
            with stats.time_phase("broken"):
                raise RuntimeError("boom")
        assert "broken" in stats.phase_timings
        assert stats.phase_timings["broken"] >= 0


class TestRecordResolution:
    @pytest.mark.parametrize(
        "tag,bucket,counter",
        [
            ("lldp", "lldp", "pairs_matched"),
            ("cdp", "cdp", "pairs_matched"),
            ("cam-dataless", "cam", "resolved_single_dataless"),
            ("cam-return", "cam", "resolved_return_path"),
        ],
    )
    def test_when_tag_is_known_then_record_resolution_should_bump_counter(
        self, tag, bucket, counter
    ):
        stats = ReducerStats()
        stats.record_resolution(tag, "src", "dst")
        assert getattr(stats, bucket)[counter] == 1

    def test_when_tag_is_unknown_then_record_resolution_should_raise(self):
        stats = ReducerStats()
        with pytest.raises(KeyError):
            stats.record_resolution("bogus", "src", "dst")


class TestCamDegreeBucket:
    @pytest.mark.parametrize(
        "degree,expected",
        [(1, 1), (2, 2), (3, 3), (4, 4), (5, 4), (99, 4)],
    )
    def test_when_degree_is_given_then_bucket_should_clamp_at_four(
        self, degree, expected
    ):
        assert ReducerStats().cam_degree_bucket(degree) == expected


class TestSummaryLine:
    def test_when_run_has_no_data_then_summary_should_still_render(self):
        line = ReducerStats().summary_line()
        assert "navtopology --l2 finished" in line
        assert "candidates" in line
        assert "links" in line
        assert "phases" in line

    def test_when_counters_are_set_then_summary_should_include_their_values(self):
        stats = ReducerStats()
        stats.load["candidates"] = 4127
        stats.load["filtered_admin_down"] = 312
        stats.lldp["pairs_matched"] = 582
        stats.cdp["pairs_matched"] = 47
        stats.cam["resolved_single_dataless"] = 12
        stats.cam["resolved_return_path"] = 71
        stats.aggregates["removed"] = 9
        stats.save["rows_actually_updated"] = 14
        stats.save["cleared_nontouched"] = 3
        stats.save["cleared_mismatched_state"] = 0
        stats.phase_timings["load"] = 0.31
        stats.cam_by_degree[1] = 75
        stats.cam_by_degree[2] = 8
        stats.cam_by_degree[4] = 2

        line = stats.summary_line()

        assert "4127 candidates" in line
        assert "312 admin-down" in line
        assert "582 lldp" in line
        assert "47 cdp" in line
        assert "83 cam" in line  # 12 + 71 resolved via cam
        assert "9 aggregates suppressed" in line
        assert "14 updated" in line
        assert "3 cleared (nontouched)" in line
        assert "0 cleared (mismatched-state)" in line
        assert "load=0.31s" in line
        assert "1=75" in line
        assert "2=8" in line
        assert "4+=2" in line


class TestNullStats:
    def test_when_counter_is_incremented_on_nullstats_then_it_should_not_raise(self):
        null = NullStats()
        null.lldp["pairs_matched"] += 1
        null.cam["resolved_return_path"] += 5
        null.cam_by_degree[null.cam_degree_bucket(7)] += 1

    def test_when_time_phase_is_used_on_nullstats_then_it_should_be_a_no_op(self):
        null = NullStats()
        with null.time_phase("anything"):
            pass

    def test_when_record_resolution_is_called_on_nullstats_then_it_should_not_raise(
        self,
    ):
        NullStats().record_resolution("lldp", "src", "dst")

    def test_when_summary_line_is_called_on_nullstats_then_it_should_return_empty(self):
        assert NullStats().summary_line() == ""

    def test_when_total_duration_is_called_on_nullstats_then_it_should_return_zero(
        self,
    ):
        assert NullStats().total_duration() == 0.0

    def test_when_phase_timings_is_iterated_on_nullstats_then_it_should_be_empty(self):
        null = NullStats()
        assert list(null.phase_timings) == []
        assert list(null.phase_timings.items()) == []
