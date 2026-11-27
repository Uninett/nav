#
# Copyright (C) 2026 University of Oslo
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
"""Integration tests for DatabaseResult running on Django's DB connection.

These exercise the real ``django.db.connection`` code path, including the error
handling: after the migration off the legacy connection, DB-API errors surface
as ``django.db.utils.*`` exceptions rather than ``psycopg2.*`` ones, so a
malformed report definition must still be caught and reported instead of
producing an HTTP 500.
"""

from nav.report.dbresult import DatabaseResult
from nav.report.generator import ReportConfig


class TestDatabaseResult:
    def test_when_sql_is_valid_then_result_and_headers_are_populated(self, db):
        config = _config("SELECT 1 AS the_answer")

        result = DatabaseResult(config)

        assert not result.error
        assert result.result == [(1,)]
        assert result.rowcount == 1
        assert config.sql_select == ["the_answer"]

    def test_when_report_sql_is_malformed_then_error_is_set_without_raising(self, db):
        # A malformed report definition must not turn into an HTTP 500.
        result = DatabaseResult(
            _config("SELECT * FROM does_not_exist_xyz", title="broken report")
        )

        assert result.error
        assert "broken report" in result.error

    def test_when_report_input_type_is_invalid_then_data_error_is_set(self, db):
        result = DatabaseResult(_config("SELECT 'not-an-int'::integer AS n"))

        assert result.error
        assert "Data error" in result.error

    def test_when_a_report_fails_then_the_connection_stays_usable(self, db):
        # Without the savepoint, the caught error would leave the surrounding
        # test transaction in a failed state, breaking the next query.
        DatabaseResult(_config("SELECT * FROM does_not_exist_xyz"))

        result = DatabaseResult(_config("SELECT 1 AS n"))

        assert not result.error
        assert result.result == [(1,)]


def _config(sql, title="test report"):
    config = ReportConfig()
    config.sql = sql
    config.title = title
    return config
