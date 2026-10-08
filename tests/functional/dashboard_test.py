"""Playwright tests for the dashboard widgets"""

import re

import pytest
from playwright.sync_api import expect


@pytest.mark.parametrize(
    "status, message",
    [
        (500, "Could not load widget"),
        (403, "Not allowed"),
        (None, "Could not load widget"),
    ],
)
def test_when_widget_fails_to_load_then_it_should_show_error(
    authenticated_page, status, message
):
    page, base_url = authenticated_page

    def fail(route):
        if status:
            route.fulfill(status=status)
        else:
            route.abort()

    page.route(re.compile(r".*/get-user-navlet/\d+.*"), fail)
    page.goto(base_url)

    expect(page.locator(".navlet .alert-box.alert").first).to_have_text(message)
