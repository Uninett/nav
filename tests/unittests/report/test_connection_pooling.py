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
"""Tests for Django connection pooling in report system"""

import threading
from unittest.mock import patch, MagicMock
from django.db import connection

from nav.report.dbresult import DatabaseResult
from nav.report.generator import ReportConfig
from nav.report.metaIP import MetaIP
from nav.report.IPtree import get_subnets


class TestThreadSafetyWithDjangoConnections:
    """Verify concurrent report generation doesn't leak connections"""

    def test_when_concurrent_dbresult_creation_then_no_errors(self):
        """Multiple threads creating DatabaseResult should not conflict"""
        errors = []

        def create_result():
            try:
                with patch.object(connection, 'cursor') as mock_cursor:
                    mock_cursor_instance = MagicMock()
                    mock_cursor.return_value.__enter__ = MagicMock(
                        return_value=mock_cursor_instance
                    )
                    mock_cursor.return_value.__exit__ = MagicMock()
                    mock_cursor_instance.description = [MagicMock(name='col1')]
                    mock_cursor_instance.fetchall.return_value = []

                    config = ReportConfig()
                    config.make_sql = MagicMock(return_value=('SELECT 1', None))

                    DatabaseResult(config)
            except Exception as e:  # noqa: BLE001
                errors.append(str(e))

        threads = [threading.Thread(target=create_result) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent access caused errors: {errors}"

    def test_when_concurrent_metaip_access_then_no_errors(self):
        """Multiple threads accessing MetaIP should not conflict"""
        errors = []

        def access_metaip():
            try:
                with patch.object(connection, 'cursor') as mock_cursor:
                    mock_cursor_instance = MagicMock()
                    mock_cursor.return_value.__enter__ = MagicMock(
                        return_value=mock_cursor_instance
                    )
                    mock_cursor.return_value.__exit__ = MagicMock()
                    mock_cursor_instance.fetchall.return_value = []

                    # Reset cache to force database access
                    MetaIP.MetaMap = None
                    result = MetaIP._createMetaMap(4)
                    assert result is not None
            except Exception as e:  # noqa: BLE001
                errors.append(str(e))

        threads = [threading.Thread(target=access_metaip) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent access caused errors: {errors}"

    def test_when_concurrent_iptree_access_then_no_errors(self):
        """Multiple threads calling get_subnets should not conflict"""
        errors = []

        def call_get_subnets():
            try:
                with patch.object(connection, 'cursor') as mock_cursor:
                    mock_cursor_instance = MagicMock()
                    mock_cursor.return_value.__enter__ = MagicMock(
                        return_value=mock_cursor_instance
                    )
                    mock_cursor.return_value.__exit__ = MagicMock()
                    mock_cursor_instance.fetchall.return_value = []

                    from nav.ip import IP

                    network = IP('192.168.0.0/16')
                    result = get_subnets(network)
                    assert result == []
            except Exception as e:  # noqa: BLE001
                errors.append(str(e))

        threads = [threading.Thread(target=call_get_subnets) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Concurrent access caused errors: {errors}"
