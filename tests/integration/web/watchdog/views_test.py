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
"""Integration tests for the Watchdog web endpoints."""

import pytest

from django.urls import reverse


WATCHDOG_FRAGMENT_URLS = [
    "watchdog-netbox",
    "watchdog-arp",
    "watchdog-cam",
    "watchdog-serial-numbers",
    "watchdog-active-addresses",
    "watchdog-db-size",
]


def test_when_logged_in_then_watchdog_index_should_respond_with_200(client):
    response = client.get(reverse("watchdog-index"))
    assert response.status_code == 200


@pytest.mark.parametrize("url_name", WATCHDOG_FRAGMENT_URLS)
def test_when_logged_in_then_watchdog_fragment_endpoint_should_respond_with_200(
    client, url_name
):
    response = client.get(reverse(url_name))
    assert response.status_code == 200
