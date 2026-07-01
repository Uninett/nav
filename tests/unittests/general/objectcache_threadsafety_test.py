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

    def test_when_duplicate_key_inserted_then_new_connection_is_closed(self):
        """Test that duplicate connections are closed to prevent leaks"""
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

        # conn2 should be closed to prevent leak
        self.assertTrue(
            conn2.closed, "Duplicate connection should be closed to prevent leak"
        )
        # conn1 should still be open
        self.assertFalse(conn1.closed, "Original cached connection should remain open")
