#
# Copyright (C) 2026 Universitetet i Oslo
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
from psycopg2.extensions import TRANSACTION_STATUS_IDLE

from nav.db import getConnection


def test_when_pinging_then_connection_should_be_left_idle():
    """Regression for #4135: the ping run by getConnection() must not leave
    the cached connection stuck idle in transaction.
    """
    conn = getConnection('default')
    conn.rollback()
    # A second call invalidates (and thus pings) the cached connection.
    getConnection('default')

    assert conn.info.transaction_status == TRANSACTION_STATUS_IDLE


def test_when_pinging_then_uncommitted_write_should_survive():
    """Data-loss guard: getConnection() pings every cached connection, and all
    db.conf aliases share one connection, so a ping must not roll back writes
    another caller has pending on it.
    """
    conn = getConnection('default')
    conn.rollback()
    cursor = conn.cursor()
    cursor.execute("CREATE TEMP TABLE ping_test (id integer)")
    conn.commit()
    try:
        cursor.execute("INSERT INTO ping_test VALUES (1)")
        # Another caller gets a connection, pinging the shared one mid-write.
        getConnection('default')
        conn.commit()

        cursor.execute("SELECT count(*) FROM ping_test")
        assert cursor.fetchone()[0] == 1
    finally:
        cursor.execute("DROP TABLE ping_test")
        conn.commit()
