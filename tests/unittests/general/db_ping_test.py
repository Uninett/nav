#
# Copyright (C) 2026 Sikt
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
from unittest.mock import MagicMock

from nav.db import ConnectionObject


class TestConnectionObjectPing:
    def test_when_pinging_then_it_should_execute_select_1(self):
        connection = MagicMock()
        conn_object = ConnectionObject(connection, key=('nav', 'nav'))

        conn_object.ping()

        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.execute.assert_called_once_with('SELECT 1')

    def test_when_pinging_then_it_should_roll_back_to_avoid_idle_in_transaction(self):
        connection = MagicMock()
        conn_object = ConnectionObject(connection, key=('nav', 'nav'))

        conn_object.ping()

        connection.rollback.assert_called_once()
