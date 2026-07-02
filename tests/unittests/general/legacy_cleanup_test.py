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
"""Tests for legacy database connection cleanup"""

from unittest.mock import MagicMock, patch

import psycopg2

from nav import db
from nav.db import ConnectionObject
from nav.django.legacy import LegacyCleanupMiddleware


def _cache_with(*connections):
    """Builds an ObjectCache-like dict of ConnectionObjects wrapping the given
    mock connections.
    """
    cache = {}
    for i, conn in enumerate(connections):
        cache[i] = ConnectionObject(conn, key=i)
    return cache


class TestLegacyCleanupMiddleware:
    def test_when_cached_connection_is_closed_then_it_should_not_be_rolled_back(self):
        closed = MagicMock()
        closed.closed = 1
        closed.rollback.side_effect = psycopg2.InterfaceError("already closed")

        with patch.object(db, '_connection_cache', _cache_with(closed)):
            middleware = LegacyCleanupMiddleware(get_response=MagicMock())
            response = MagicMock()
            # Must not raise even though rollback() would fail
            assert middleware.process_response(None, response) is response

        closed.rollback.assert_not_called()

    def test_when_cached_connection_is_open_then_it_should_be_rolled_back(self):
        open_conn = MagicMock()
        open_conn.closed = 0

        with patch.object(db, '_connection_cache', _cache_with(open_conn)):
            middleware = LegacyCleanupMiddleware(get_response=MagicMock())
            middleware.process_response(None, MagicMock())

        open_conn.rollback.assert_called_once()


class TestCloseConnections:
    def test_when_closing_connections_then_cache_should_be_emptied(self):
        conn = MagicMock()

        with patch.object(db, '_connection_cache', _cache_with(conn)):
            db.closeConnections()
            conn.close.assert_called_once()
            assert len(db._connection_cache) == 0
