import subprocess

import pytest
from playwright.sync_api import Page

from nav.django.defaults import NAV_LOGIN_URL as LOGIN_URL


def pytest_configure(config):
    _ensure_playwright_browser()


def _ensure_playwright_browser():
    """Download the Chromium binary if not already present."""
    subprocess.check_call(["playwright", "install", "chromium"])


@pytest.fixture
def authenticated_page(page: Page, live_server, admin_username, admin_password):
    """Fixture providing a Playwright page logged in as admin"""
    page.goto(f"{live_server}{LOGIN_URL}")
    page.locator("#id_username").fill(admin_username)
    page.locator("#id_password").fill(admin_password)
    page.locator("#submit-id-submit").click()
    page.wait_for_url(f"{live_server}/")
    yield page, live_server
