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
"""Console-error smoke test for JS-heavy pages.

The karma unit suite (python/nav/web/static/js/test/) can't catch page-wide
load failures: it exercises isolated functions, never a full page. This
loads several pages as an authenticated user via Playwright and asserts
each one actually loaded (HTTP 200) with a clean browser console: no
uncaught exceptions, no error/warning-level console messages.

Uses `fresh_authenticated_page` rather than `authenticated_page` so the
console listeners are attached to a page that has never visited the
dashboard -- the dashboard's own background requests would otherwise be a
source of unrelated console noise for whichever page a given test case
happens to load next.

Anything thrown after the page reaches networkidle is missed; that's an
accepted tradeoff for a fast, broad smoke test, not a guarantee of full
coverage.
"""

from django.conf import settings
from django.shortcuts import resolve_url
import pytest

# Pages that render meaningfully on an empty/fresh test DB. IPAM and the
# room-rack Vue widget need seeded fixtures and aren't here yet -- IPAM in
# particular currently throws its own (pre-existing, unrelated) Marionette
# error when no "scope" prefix is seeded, worth its own fix separately.
PAGES = [
    ("status", "/status/"),
    ("netmap", "/netmap/"),
    ("home", "/"),
    ("portadmin", "/portadmin/"),
    ("seeddb", "/seeddb/"),
    ("interface_browser", "/interfaces/"),
    ("ipdevinfo", "/ipdevinfo/"),
    ("syslogger", "/syslogger/"),
    ("neighbors", "/neighbors/"),
    ("business", "/business/"),
    ("machinetracker", "/machinetracker/"),
    ("threshold", "/threshold/"),
    ("alertprofiles", "/alertprofiles/"),
    ("radius", "/radius/"),
    ("report", "/report/"),
    ("networkexplorer", "/networkexplorer/"),
    ("arnold", "/arnold/"),
]

# Fail fast rather than eat the default 30s per page if one hangs.
NETWORKIDLE_TIMEOUT_MS = 10_000


@pytest.mark.parametrize("path", [pytest.param(path, id=name) for name, path in PAGES])
def test_when_loading_page_then_it_should_have_no_console_errors(
    fresh_authenticated_page, path
):
    page, base_url = fresh_authenticated_page
    errors = _watch_console_errors(page)

    response = page.goto(f"{base_url}{path}")
    page.wait_for_load_state("networkidle", timeout=NETWORKIDLE_TIMEOUT_MS)

    assert response.status == 200, f"{path} returned HTTP {response.status}"
    assert not errors, f"Console errors on {path}: {errors}"


def test_when_loading_login_then_it_should_have_no_console_errors(page, live_server):
    errors = _watch_console_errors(page)

    response = page.goto(f"{live_server}{resolve_url(settings.LOGIN_URL)}")
    page.wait_for_load_state("networkidle", timeout=NETWORKIDLE_TIMEOUT_MS)

    assert response.status == 200, f"Login page returned HTTP {response.status}"
    assert not errors, f"Console errors on login page: {errors}"


def _watch_console_errors(page) -> list[str]:
    """Arm listeners and return the list they'll append to as events arrive.

    Catches uncaught exceptions (pageerror) and error/warning-level console
    messages. jQuery's own Deferred exception reporting logs at "warning"
    level rather than "error", which is why both are watched here.
    """
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on(
        "console",
        lambda msg: (
            errors.append(f"[console.{msg.type}] {msg.text}")
            if msg.type in ("error", "warning")
            else None
        ),
    )
    return errors
