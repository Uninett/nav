from nav.django.defaults import NAV_LOGIN_URL as LOGIN_URL

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
    page.goto(f"{live_server}{LOGIN_URL}")
    page.locator("#id_username").fill(admin_username)
    page.locator("#id_password").fill(admin_password)
    page.locator("#submit-id-submit").click()
    page.wait_for_url(f"{live_server}/")
    yield page, live_server
