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
"""Tests for nav.db thread-local connection caching"""

import threading
from unittest.mock import MagicMock, patch

from nav import db, ObjectCache


PARAMS = ('host', 5432, 'nav', 'navuser', 'secret')
CACHE_KEY = ('nav', 'navuser')


class TestThreadLocalConnectionCache:
    def test_when_called_in_same_thread_twice_then_connection_is_reused(self):
        conn = MagicMock(name='conn')

        with (
            patch.object(db, 'get_connection_parameters', return_value=PARAMS),
            patch.object(db.psycopg2, 'connect', return_value=conn) as connect,
        ):
            first = db.getConnection('default')
            second = db.getConnection('default')

        assert first is conn
        assert second is conn
        connect.assert_called_once()

    def test_when_called_in_separate_threads_then_connections_are_distinct(self):
        connections = {}

        def fake_connect(_dsn):
            # A distinct connection object per invocation.
            return MagicMock(name='conn')

        def worker(name):
            with (
                patch.object(db, 'get_connection_parameters', return_value=PARAMS),
                patch.object(db.psycopg2, 'connect', side_effect=fake_connect),
            ):
                connections[name] = db.getConnection('default')

        threads = [threading.Thread(target=worker, args=(name,)) for name in ('a', 'b')]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert connections['a'] is not connections['b']

    def test_when_accessed_from_separate_threads_then_caches_are_distinct(self):
        caches = {}

        def worker(name):
            caches[name] = db._get_connection_cache()

        threads = [threading.Thread(target=worker, args=(name,)) for name in ('a', 'b')]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert isinstance(caches['a'], ObjectCache)
        assert isinstance(caches['b'], ObjectCache)
        assert caches['a'] is not caches['b']

    def test_when_cache_is_empty_then_new_connection_is_opened_and_cached(self):
        conn = MagicMock(name='conn')

        def worker():
            with (
                patch.object(db, 'get_connection_parameters', return_value=PARAMS),
                patch.object(db.psycopg2, 'connect', return_value=conn) as connect,
            ):
                result = db.getConnection('default')
                cache = db._get_connection_cache()

                assert result is conn
                assert cache[CACHE_KEY].object is conn
                connect.assert_called_once()
                conn.close.assert_not_called()

        # Run in a fresh thread to guarantee an empty thread-local cache.
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
