"""pytest setup and fixtures common for all tests, regardless of suite"""

import os
import platform
import subprocess

import pytest
import requests
from requests.adapters import HTTPAdapter, Retry


def pytest_configure(config):
    # Bootstrap Django config
    from nav.bootstrap import bootstrap_django

    bootstrap_django('pytest')

    # Setup test environment for Django
    from django.test.utils import setup_test_environment

    setup_test_environment()

    if platform.system() == 'Linux':
        # Install custom reactor for Twisted tests
        from nav.ipdevpoll.epollreactor2 import install

        install()


@pytest.fixture(scope='session')
def admin_username():
    return os.environ.get('ADMINUSERNAME', 'admin')


@pytest.fixture(scope='session')
def admin_password():
    return os.environ.get('ADMINPASSWORD', 'admin')


@pytest.fixture(scope='session')
def gunicorn():
    """Sets up NAV to be served by a gunicorn instance.

    Useful for tests that need to make external HTTP requests to NAV.

    Returns the (expected) base URL of the gunicorn instance.
    """
    workspace = os.path.join(os.environ.get('WORKSPACE', ''), 'reports')
    errorlog = os.path.join(workspace, 'gunicorn-error.log')
    accesslog = os.path.join(workspace, 'gunicorn-access.log')
    gunicorn = subprocess.Popen(
        [
            'gunicorn',
            '--error-logfile',
            errorlog,
            '--access-logfile',
            accesslog,
            'navtest_wsgi:application',
        ]
    )
    # Allow for gunicorn to become ready to serve requests before handing off to a test
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    base_url = "http://localhost:8000"
    session.mount(base_url, HTTPAdapter(max_retries=retries))
    session.get(base_url)

    yield base_url

    gunicorn.terminate()
