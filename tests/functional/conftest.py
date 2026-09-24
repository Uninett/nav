import pytest
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.test.testcases import LiveServerThread
from playwright.sync_api import Page

########################################################################
#                                                                      #
# Set up the required components for a functional test. PostgreSQL is  #
# assumed to already be available, with connection details in the PG*  #
# environment variables.  The connecting role must have CREATEDB       #
# privileges.                                                          #
#                                                                      #
########################################################################


def pytest_configure(config):
    from ..setup_test_config import ensure_config_dir, create_test_database

    ensure_config_dir()
    create_test_database()
    _ensure_playwright_browser()


def _ensure_playwright_browser():
    """Download the Chromium binary if not already present."""
    import subprocess

    subprocess.check_call(["playwright", "install", "chromium"])


@pytest.fixture(scope='session')
def live_server():
    """Start a threaded Django live server for functional tests"""
    server_thread = LiveServerThread('localhost', StaticFilesHandler, port=0)
    server_thread.daemon = True
    server_thread.start()
    server_thread.is_ready.wait()
    if server_thread.error:
        raise server_thread.error
    yield f'http://{server_thread.host}:{server_thread.port}'
    server_thread.terminate()
    server_thread.join()


@pytest.fixture
def authenticated_page(page: Page, live_server, admin_username, admin_password):
    """Fixture providing a Playwright page logged in as admin"""
    # Imported lazily: importing nav.django.settings at conftest module level
    # would lock in Django's settings before the DB fixtures configure it.
    from django.conf import settings
    from django.shortcuts import resolve_url

    page.goto(f"{live_server}{resolve_url(settings.LOGIN_URL)}")
    page.locator("#id_login").fill(admin_username)
    page.locator("#id_password").fill(admin_password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server}/")
    yield page, live_server


@pytest.fixture(scope='session')
def admin_storage_state(browser, live_server, admin_username, admin_password):
    """Log in once per session and return the resulting Playwright storage state.

    Reusing this avoids repeating a full interactive login (and the
    dashboard load that follows it) for every test that just needs an
    authenticated session and doesn't care how it got one.
    """
    from django.conf import settings
    from django.shortcuts import resolve_url

    context = browser.new_context()
    page = context.new_page()
    page.goto(f"{live_server}{resolve_url(settings.LOGIN_URL)}")
    page.locator("#id_login").fill(admin_username)
    page.locator("#id_password").fill(admin_password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url(f"{live_server}/")
    state = context.storage_state()
    context.close()
    return state


@pytest.fixture
def fresh_authenticated_page(browser, admin_storage_state, live_server):
    """An authenticated Playwright page that has never visited any NAV page.

    Unlike `authenticated_page`, this doesn't land on the dashboard as a
    side effect of logging in -- the session cookie comes from
    `admin_storage_state` instead. Use this when a test needs to control
    exactly what the first page load is, e.g. to listen for console errors
    without picking up noise from an unrelated page the login flow happened
    to visit.
    """
    context = browser.new_context(storage_state=admin_storage_state)
    page = context.new_page()
    yield page, live_server
    context.close()
