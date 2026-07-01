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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Tests for ObjectCache thread safety"""

import threading
from unittest import TestCase

from nav import CacheError, ObjectCache, CacheableObject


class MockConnection:
    """Mock database connection for testing"""

    def __init__(self, name):
        self.name = name
        self.closed = False

    def close(self):
        self.closed = True

    def __repr__(self):
        return f"MockConnection({self.name})"


class ObjectCacheThreadSafetyTest(TestCase):
    def setUp(self):
        self.cache = ObjectCache()

    def test_when_concurrent_insertions_then_only_one_succeeds(self):
        """Test that concurrent insertions of the same key don't cause issues"""
        key = ('test', 'key')
        errors = []

        def insert_connection(conn_id):
            try:
                conn = MockConnection(f"conn_{conn_id}")
                obj = CacheableObject(conn)
                obj.key = key
                self.cache.cache(obj)
            except CacheError as e:
                errors.append(e)

        # Spawn 10 threads trying to cache the same key simultaneously
        threads = []
        for i in range(10):
            t = threading.Thread(target=insert_connection, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Exactly one should succeed, the rest should get CacheError
        self.assertEqual(len(errors), 9, "Expected 9 threads to fail with CacheError")
        self.assertIn(key, self.cache, "Key should be in cache")

        # The cached connection should NOT be closed
        cached_obj = self.cache[key]
        self.assertFalse(
            cached_obj.object.closed, "Cached connection should remain open"
        )

    def test_when_duplicate_key_inserted_then_cache_error_is_raised(self):
        """A duplicate insert must raise CacheError and leave the cache and the
        stored objects untouched. Disposing of the redundant object is the
        caller's responsibility, not the cache's.
        """
        key = ('test', 'key')

        # Cache first connection
        conn1 = MockConnection("conn1")
        obj1 = CacheableObject(conn1)
        obj1.key = key
        self.cache.cache(obj1)

        # Try to cache second connection with same key
        conn2 = MockConnection("conn2")
        obj2 = CacheableObject(conn2)
        obj2.key = key

        with self.assertRaises(CacheError):
            self.cache.cache(obj2)

        # The cache must not touch either connection
        self.assertFalse(conn2.closed, "Cache must not close the caller's object")
        self.assertFalse(conn1.closed, "Original cached connection should remain open")
        self.assertIs(self.cache[key], obj1, "Winning object should remain cached")

    def test_when_cleared_then_cache_is_emptied_and_items_uncached(self):
        """clear() must empty the cache and detach every stored object so no
        stale back-reference to the cache lingers.
        """
        obj = CacheableObject(MockConnection("conn"))
        obj.key = ('test', 'key')
        self.cache.cache(obj)

        self.cache.clear()

        self.assertEqual(len(self.cache), 0, "Cache should be empty after clear()")
        self.assertIsNone(obj.cache, "Cleared object should be detached from cache")
