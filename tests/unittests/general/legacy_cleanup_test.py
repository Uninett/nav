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
    def test_when_rollback_fails_on_dead_connection_then_cleanup_should_not_raise(
        self,
    ):
        # A connection killed out-of-band (e.g. a database reboot) raises on
        # rollback rather than being flagged as closed beforehand.
        dead = MagicMock()
        dead.rollback.side_effect = psycopg2.OperationalError(
            "server closed the connection unexpectedly"
        )

        with patch.object(db, '_connection_cache', _cache_with(dead)):
            middleware = LegacyCleanupMiddleware(get_response=MagicMock())
            response = MagicMock()
            # Must not raise even though rollback() fails
            assert middleware.process_response(None, response) is response

        dead.rollback.assert_called_once()

    def test_when_cached_connection_is_healthy_then_it_should_be_rolled_back(self):
        healthy = MagicMock()

        with patch.object(db, '_connection_cache', _cache_with(healthy)):
            middleware = LegacyCleanupMiddleware(get_response=MagicMock())
            middleware.process_response(None, MagicMock())

        healthy.rollback.assert_called_once()
