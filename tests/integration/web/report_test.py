#
# Copyright (C) 2026 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Tests that untrusted input cannot inject markup into reports"""

import pytest
from django.core.cache import cache
from django.urls import reverse

from nav.models.manage import Room

MARKER = "<b>xss-marker</b>"
ESCAPED_MARKER = "&lt;b&gt;xss-marker&lt;/b&gt;"


@pytest.mark.parametrize("view_name", ["report-by-name", "widget-report-by-name"])
def test_when_room_description_has_markup_then_report_should_escape_it(
    client, room_with_markup_description, view_name
):
    url = reverse(view_name, kwargs={"report_name": "room"})
    response = client.get(url, {"roomid": room_with_markup_description})

    content = response.content.decode("utf-8")
    assert ESCAPED_MARKER in content
    assert MARKER not in content


@pytest.fixture(autouse=True)
def empty_report_cache():
    """Keeps report results cached by earlier requests or test runs from
    masking the output of the code under test.
    """
    cache.clear()


@pytest.fixture
def room_with_markup_description():
    """Creates a room whose description holds markup.

    The report generator may read through a different database connection than
    Django's, so this deliberately avoids the transactional ``db`` fixture. The
    room is committed here and removed again afterwards.
    """
    room = Room.objects.create(
        id="xssroom", location_id="mylocation", description=MARKER
    )
    yield room.id

    room.delete()
