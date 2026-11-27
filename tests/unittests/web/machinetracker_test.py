from datetime import datetime, timedelta
from types import SimpleNamespace

from nav.models.fields import INFINITY
from nav.web.machinetracker.utils import collapse_overlapping


class TestCollapseOverlapping:
    def test_given_overlapping_active_rows_it_should_merge_span_and_sources(self):
        now = datetime.now()
        rows = [
            _row(now - timedelta(hours=1), INFINITY, "router-a"),
            _row(now - timedelta(hours=2), INFINITY, "router-b"),
        ]
        kept = collapse_overlapping(rows)
        assert len(kept) == 1
        assert kept[0].start_time == now - timedelta(hours=2)
        assert kept[0].end_time == INFINITY
        assert kept[0].still_active
        assert kept[0].sysname == "router-b, router-a"

    def test_given_open_older_and_newer_closed_it_should_keep_address_active(self):
        # HSRP: active router has held the entry since Monday; standby learned
        # it briefly today. The merged row must still show the address as here.
        monday = datetime.now() - timedelta(days=3)
        rows = [
            _row(monday, INFINITY, "gw-a"),
            _row(
                datetime.now() - timedelta(hours=4),
                datetime.now() - timedelta(hours=2),
                "gw-b",
            ),
        ]
        kept = collapse_overlapping(rows)
        assert len(kept) == 1
        assert kept[0].start_time == monday
        assert kept[0].end_time == INFINITY
        assert kept[0].still_active
        assert kept[0].sysname == "gw-a, gw-b"

    def test_given_adjacent_rows_it_should_keep_them_separate(self):
        now = datetime.now()
        boundary = now - timedelta(hours=2)
        rows = [
            _row(boundary, now, "router-a"),
            _row(now - timedelta(hours=4), boundary, "router-a"),
        ]
        kept = collapse_overlapping(rows)
        assert len(kept) == 2

    def test_given_open_row_it_should_absorb_later_rows_past_a_short_one(self):
        # The open row stays the group's latest end_time, so a row starting
        # after an intervening short row still merges instead of splitting off.
        now = datetime.now()
        rows = [
            _row(now - timedelta(hours=5), INFINITY, "router-a"),
            _row(now - timedelta(hours=4), now - timedelta(hours=3), "router-b"),
            _row(now - timedelta(hours=2), now - timedelta(hours=1), "router-c"),
        ]
        kept = collapse_overlapping(rows)
        assert len(kept) == 1
        assert kept[0].start_time == now - timedelta(hours=5)
        assert kept[0].end_time == INFINITY

    def test_given_disjoint_rows_it_should_keep_them_separate(self):
        now = datetime.now()
        rows = [
            _row(now - timedelta(hours=1), now, "router-a"),
            _row(now - timedelta(hours=4), now - timedelta(hours=3), "router-a"),
        ]
        kept = collapse_overlapping(rows)
        assert len(kept) == 2

    def test_given_overlapping_run_plus_disjoint_it_should_merge_only_the_run(self):
        now = datetime.now()
        rows = [
            _row(now - timedelta(hours=1), INFINITY, "router-a"),
            _row(now - timedelta(hours=2), INFINITY, "router-b"),
            _row(now - timedelta(hours=5), now - timedelta(hours=4), "router-a"),
        ]
        kept = collapse_overlapping(rows)
        assert len(kept) == 2
        merged = max(kept, key=lambda r: r.start_time)
        assert merged.start_time == now - timedelta(hours=2)
        assert merged.end_time == INFINITY


def _row(start, end, sysname, ip="10.0.0.42", mac="ca:fe:ba:be:f0:01"):
    return SimpleNamespace(
        ip=ip,
        mac=mac,
        start_time=start,
        end_time=end,
        sysname=sysname,
    )
