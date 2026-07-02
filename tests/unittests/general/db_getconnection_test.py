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
"""Tests for nav.db.getConnection connection caching"""

from unittest.mock import MagicMock, patch

import nav
from nav import db, ObjectCache
from nav.db import ConnectionObject


PARAMS = ('host', 5432, 'nav', 'navuser', 'secret')
CACHE_KEY = ('nav', 'navuser')


class TestGetConnectionRace:
    def test_when_another_thread_wins_the_cache_race_then_winner_is_returned(self):
        """A losing thread must reuse the winner's cached connection instead of
        propagating the CacheError raised by the duplicate insert.
        """
        cache = ObjectCache()
        winner = MagicMock(name='winner')
        loser = MagicMock(name='loser')

        def fake_connect(_dsn):
            # Simulate the winning thread caching its connection between our
            # cache miss and our own insert attempt.
            if CACHE_KEY not in cache:
                cache.cache(ConnectionObject(winner, CACHE_KEY))
            return loser

        with (
            patch.object(db, '_connection_cache', cache),
            patch.object(db, 'get_connection_parameters', return_value=PARAMS),
            patch.object(db.psycopg2, 'connect', side_effect=fake_connect),
        ):
            result = db.getConnection('default')

        assert result is winner, "Loser should reuse the winner's connection"
        loser.close.assert_called_once()
        assert cache[CACHE_KEY].object is winner

    def test_when_no_race_then_new_connection_is_cached_and_returned(self):
        cache = ObjectCache()
        conn = MagicMock(name='conn')

        with (
            patch.object(db, '_connection_cache', cache),
            patch.object(db, 'get_connection_parameters', return_value=PARAMS),
            patch.object(db.psycopg2, 'connect', return_value=conn),
        ):
            result = db.getConnection('default')

        assert result is conn
        assert cache[CACHE_KEY].object is conn
        conn.close.assert_not_called()

    def test_when_winner_is_evicted_before_reuse_then_a_fresh_connection_opens(self):
        """If the winning entry is invalidated and evicted between our failed
        insert and the reuse lookup, getConnection must retry and open a fresh
        connection rather than crash on the missing cache entry.
        """

        class FlakyCache(ObjectCache):
            """Fails the first insert (as if a racing thread held the key) but
            reports the key as already gone, forcing getConnection to retry.
            """

            def __init__(self):
                super().__init__()
                self._first_insert = True

            def cache(self, item):
                if self._first_insert:
                    self._first_insert = False
                    raise nav.CacheError("simulated race")
                super().cache(item)

            def get(self, key, default=None):
                # The winner was evicted before we could read it.
                return None

        cache = FlakyCache()
        loser = MagicMock(name='loser')
        fresh = MagicMock(name='fresh')
        conns = [loser, fresh]

        with (
            patch.object(db, '_connection_cache', cache),
            patch.object(db, 'get_connection_parameters', return_value=PARAMS),
            patch.object(db.psycopg2, 'connect', side_effect=lambda _dsn: conns.pop(0)),
        ):
            result = db.getConnection('default')

        assert result is fresh, "Should retry and return a freshly opened connection"
        loser.close.assert_called_once()
        assert cache[CACHE_KEY].object is fresh
