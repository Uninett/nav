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


@pytest.mark.parametrize("name", ["", "   ", "\t"])
def test_when_adding_dashboard_with_blank_name_then_it_should_show_error(
    authenticated_page, name
):
    page, base_url = authenticated_page
    page.goto(base_url)

    page.get_by_title("Add new dashboard").click()
    form = page.locator("#form-add-dashboard")
    form.locator("input[name='dashboard-name']").fill(name)
    form.get_by_role("button", name="Add dashboard").click()

    expect(form.locator(".error")).to_have_text("Dashboard name must not be empty")


@pytest.mark.parametrize("name", ["", "   ", "\t"])
def test_when_renaming_dashboard_to_blank_name_then_it_should_show_error(
    authenticated_page, name
):
    page, base_url = authenticated_page
    page.goto(base_url)

    page.get_by_title("Settings for current dashboard").click()
    form = page.locator("#form-rename-dashboard")
    form.locator("input[name='dashboard-name']").fill(name)
    form.get_by_role("button", name="Rename dashboard").click()

    expect(form.locator(".error")).to_have_text("Dashboard name must not be empty")
