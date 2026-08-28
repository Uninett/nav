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
"""Tests for the geomap data view's database access"""

from unittest.mock import MagicMock, patch

import psycopg2.extras
from django.test import RequestFactory

from nav.web.geomap import views


QUERY = {
    'format': 'geojson',
    'limit': '30',
    'viewportWidth': '800',
    'viewportHeight': '600',
    'create_edges': 'true',
    'fetch_data': 'false',
    'bbox': '10.0,63.0,10.5,63.5',
}


def test_when_serving_geomap_data_then_django_managed_connection_is_used():
    """The view must fetch its DictCursor from the Django-managed connection
    (not the legacy nav.db cache) and must never close that connection itself.
    """
    request = RequestFactory().get('/geomap/normal/data', QUERY)

    cursor = MagicMock(name='cursor')
    fake_connection = MagicMock(name='db_connection')
    # cursor(...) is used as a context manager: `with ... as db`
    fake_connection.connection.cursor.return_value.__enter__.return_value = cursor

    with (
        patch.object(views, 'db_connection', fake_connection),
        patch.object(views, 'get_formatted_data', return_value='DATA') as get_data,
        patch.object(views, 'format_mime_type', return_value='application/json'),
    ):
        response = views.data(request, 'normal')

    assert response.status_code == 200
    assert response.content == b'DATA'

    # Django connection was established and a DictCursor requested from it
    fake_connection.ensure_connection.assert_called_once()
    fake_connection.connection.cursor.assert_called_once_with(
        cursor_factory=psycopg2.extras.DictCursor
    )
    # The cursor from that connection is what gets handed to the query layer
    assert get_data.call_args.args[1] is cursor
    # We must not close the shared Django connection
    fake_connection.connection.close.assert_not_called()
    fake_connection.close.assert_not_called()
