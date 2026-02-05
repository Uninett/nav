import os
import subprocess

import pytest
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.test.testcases import LiveServerThread
from playwright.sync_api import Page

USERNAME = 'admin'

if os.environ.get('WORKSPACE'):
    SCRIPT_PATH = os.path.join(os.environ['WORKSPACE'], 'tests/docker/scripts')
else:
    SCRIPT_PATH = '/'
SCRIPT_CREATE_DB = os.path.join(SCRIPT_PATH, 'create-db.sh')


def pytest_configure(config):
    subprocess.check_call([SCRIPT_CREATE_DB])


@pytest.fixture(scope='session')
def live_server():
    """Start a threaded Django live server for functional tests."""
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
    """Fixture providing a Playwright page logged in as admin."""
    page.goto(f"{live_server}/index/login")
    page.locator("#id_username").fill(admin_username)
    page.locator("#id_password").fill(admin_password)
    page.locator("input[name='submit']").click()
    page.wait_for_url(f"{live_server}/")
    yield page, live_server
