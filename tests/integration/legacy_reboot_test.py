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
"""Integration tests for legacy DB cleanup surviving a PostgreSQL reboot.

Rebooting the database server (which happens in production from time to time)
terminates every backend, so any legacy connection cached in
``nav.db._connection_cache`` becomes dead. ``LegacyCleanupMiddleware`` rolls
back every cached connection on each response; rolling back a dead connection
must not turn request cleanup into an HTTP 500.
"""

import psycopg2
import pytest

import nav.db
from nav.db import (
    get_connection_parameters,
    get_connection_string,
    getConnection,
)
from nav.django.legacy import LegacyCleanupMiddleware


@pytest.fixture
def admin_connection():
    """A separate connection used to terminate the cached backend."""
    conn = psycopg2.connect(get_connection_string(get_connection_parameters('default')))
    conn.autocommit = True
    yield conn
    conn.close()


def _kill_backend(admin_conn, pid):
    """Terminate the given backend, as a server reboot would."""
    with admin_conn.cursor() as cur:
        cur.execute("SELECT pg_terminate_backend(%s)", (pid,))


class TestLegacyCleanupAfterDatabaseReboot:
    def test_when_reboot_kills_backend_then_connection_is_not_yet_marked_closed(
        self, db, admin_connection
    ):
        """psycopg2 does not flag a connection closed until the next I/O.

        This documents why a plain ``if conn.closed`` guard in the middleware is
        not enough: right after the reboot the dead connection still looks open.
        """
        conn = getConnection('default')
        with conn.cursor() as cur:
            cur.execute("SELECT 1")

        _kill_backend(admin_connection, conn.get_backend_pid())

        assert conn.closed == 0

    def test_cleanup_should_not_raise_when_cached_connection_died_in_reboot(
        self, db, admin_connection
    ):
        conn = getConnection('default')
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        assert conn in [obj.object for obj in nav.db._connection_cache.values()]

        _kill_backend(admin_connection, conn.get_backend_pid())

        middleware = LegacyCleanupMiddleware(get_response=lambda request: request)
        response = object()
        # Must not raise even though the cached connection is now dead
        assert middleware.process_response(None, response) is response
