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
"""Per-run statistics collector for the L2 topology detector.

`ReducerStats` is owned by `do_layer2_detection` and threaded through
`build_candidate_graph_from_db`, `AdjacencyReducer`, and
`update_layer2_topology` so each phase can record counters and timings.

The collector produces a single INFO-level summary log line at end of run.
Per-resolution DEBUG log lines are emitted via `record_resolution`, tagging
the source heuristic ('lldp', 'cdp', 'cam-dataless', 'cam-return').

`NullStats` is a drop-in no-op used by callers that don't care (e.g. unit
tests that exercise the reducer in isolation).

Reading the summary line
========================

The end-of-run summary line looks like this::

    navtopology --l2 finished in 1.84s: 4127 candidates (312 admin-down)
    → 712 links (582 lldp, 47 cdp, 83 cam); 14 updated, 3 cleared
    (nontouched), 0 cleared (mismatched-state); cam_by_degree: 1=75 2=8
    3=0 4+=2; phases: load=0.31s reduce.lldp=0.04s ...

Fields, in order:

* ``finished in <T>s`` — wall-clock duration of the whole L2 detection run.
* ``<N> candidates`` — rows read from ``adjacency_candidate``. The input
  size for the entire reduction.
* ``(<N> admin-down)`` — candidate rows skipped because the source
  interface is administratively down (filtered in Python, not SQL).
* ``<N> links`` — total resolved physical links written to the result
  graph. Sum of the three sources that follow.
* ``(<N> lldp, <N> cdp, <N> cam)`` — how many of those links were resolved
  by each source. LLDP and CDP each count mutual-pair matches; "cam" sums
  the two CAM heuristics (single-dataless-destination and return-path).
* ``<N> updated`` — rows in the ``interface`` table whose topology
  columns actually changed value. The Django ORM update returns this
  count; rows whose proposed value matched the existing value are
  excluded earlier in the chain. This is the load-bearing number for
  judging how much database churn the detector causes.
* ``<N> cleared (nontouched)`` — rows zeroed because no candidate
  pointed at them this run.
* ``<N> cleared (mismatched-state)`` — rows zeroed because the local
  interface is operDown but the remote claims to still be operUp (stale
  topology indicator).
* ``cam_by_degree: 1=A 2=B 3=C 4+=D`` — **starting distribution** of
  per-port CAM ambiguity, snapshotted just before ``_reduce_cam`` enters
  its main loop. A port with out-degree N has CAM evidence pointing to N
  distinct remote candidates. High ``4+`` counts mean the input data is
  noisy (e.g. uplinks observing MAC addresses bleeding through from
  downstream switches) — useful run-over-run to spot upstream issues.
  *Not* a measure of what was left unresolved; see ``cam.unresolved_remaining``
  (collected but not currently in the summary line) for that.
* ``phases: ...`` — wall-clock seconds per phase. ``load`` is candidate
  graph construction; ``reduce.{lldp,cdp,aggregates,cam}`` are the four
  reduction phases; ``save.{update,clear_nontouched,clear_mismatched_state}``
  are the three database write phases.

Operators reading ``navtopology.log`` mostly care about the wall-clock,
the resolved-links breakdown, and the ``updated`` count. Developers
debugging "why does NAV think A connects to B?" should also enable
``nav.topology = DEBUG`` to get one ``resolved: <src> -> <dst> [<tag>]``
line per resolution.
"""

import logging
import time
from collections import defaultdict
from contextlib import contextmanager

_logger = logging.getLogger(__name__)


class ReducerStats:
    """Accumulates counters and phase timings for one navtopology --l2 run.

    See the module docstring for a field-by-field interpretation of the
    summary line `summary_line()` produces.
    """

    def __init__(self):
        self._wall_start = time.monotonic()
        self.phase_timings = {}
        self.load = defaultdict(int)
        self.lldp = defaultdict(int)
        self.cdp = defaultdict(int)
        self.aggregates = defaultdict(int)
        self.cam = defaultdict(int)
        self.cam_by_degree = defaultdict(int)
        self.save = defaultdict(int)

    @contextmanager
    def time_phase(self, name):
        start = time.monotonic()
        try:
            yield
        finally:
            self.phase_timings[name] = time.monotonic() - start

    def record_resolution(self, source_tag, src, dst):
        """Bump the source-specific counter and emit a DEBUG line.

        `source_tag` is one of 'lldp', 'cdp', 'cam-dataless', 'cam-return'.
        """
        bucket, counter = _SOURCE_TAG_COUNTER[source_tag]
        getattr(self, bucket)[counter] += 1
        _logger.debug("resolved: %s -> %s [%s]", src, dst, source_tag)

    def cam_degree_bucket(self, degree):
        """Map a raw out-degree into the {1, 2, 3, 4+} histogram bucket."""
        return min(max(degree, 1), 4)

    def total_duration(self):
        return time.monotonic() - self._wall_start

    def summary_line(self):
        """Single human-readable line summarizing the run."""
        candidates = self.load["candidates"]
        admin_down = self.load["filtered_admin_down"]
        lldp_links = self.lldp["pairs_matched"]
        cdp_links = self.cdp["pairs_matched"]
        cam_links = (
            self.cam["resolved_single_dataless"] + self.cam["resolved_return_path"]
        )
        total_links = lldp_links + cdp_links + cam_links
        updated = self.save["rows_actually_updated"]
        cleared_nt = self.save["cleared_nontouched"]
        cleared_ms = self.save["cleared_mismatched_state"]

        phases = " ".join(
            f"{name}={dur:.2f}s" for name, dur in self.phase_timings.items()
        )
        degree_buckets = " ".join(
            f"{'4+' if b == 4 else b}={self.cam_by_degree[b]}" for b in (1, 2, 3, 4)
        )

        return (
            f"navtopology --l2 finished in {self.total_duration():.2f}s: "
            f"{candidates} candidates ({admin_down} admin-down) → "
            f"{total_links} links "
            f"({lldp_links} lldp, {cdp_links} cdp, {cam_links} cam); "
            f"{updated} updated, "
            f"{cleared_nt} cleared (nontouched), "
            f"{cleared_ms} cleared (mismatched-state); "
            f"cam_by_degree: {degree_buckets}; "
            f"phases: {phases}"
        )


_SOURCE_TAG_COUNTER = {
    "lldp": ("lldp", "pairs_matched"),
    "cdp": ("cdp", "pairs_matched"),
    "cam-dataless": ("cam", "resolved_single_dataless"),
    "cam-return": ("cam", "resolved_return_path"),
}


class _NullDict:
    """Dict-like that swallows all writes and returns 0 for any read.

    `__getitem__` returning 0 and `__setitem__` discarding are both required
    for `null_dict[k] += 1` (an augmented assignment) to no-op without
    accumulating state — a bare `defaultdict(int)` would leak memory on long
    runs.
    """

    def __getitem__(self, key):
        return 0

    def __setitem__(self, key, value):
        pass

    def __contains__(self, key):
        return False

    def __iter__(self):
        return iter(())

    def items(self):
        return ()


_NULL_DICT = _NullDict()


class NullStats:
    """No-op drop-in for `ReducerStats`.

    All counter attributes (`load`, `lldp`, `cdp`, `aggregates`, `cam`,
    `cam_by_degree`, `save`, `phase_timings`) yield a `_NullDict` that
    swallows writes. Methods are real but do nothing observable.

    Pinned truthy so that the `stats = stats or NullStats()` sentinel
    pattern keeps a caller-supplied instance intact even if a future
    refactor adds `__len__` or other implicitly-falsy hooks.
    """

    def __bool__(self):
        return True

    def __getattr__(self, name):
        return _NULL_DICT

    @contextmanager
    def time_phase(self, name):
        yield

    def record_resolution(self, source_tag, src, dst):
        pass

    def cam_degree_bucket(self, degree):
        return min(max(degree, 1), 4)

    def total_duration(self):
        return 0.0

    def summary_line(self):
        return ""
