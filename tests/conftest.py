"""Pytest config and fixtures for all test suites"""
import os
import platform
import subprocess

import pytest
import requests
from requests.adapters import HTTPAdapter, Retry
from retry import retry


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


def is_running_in_github_actions():
    """Returns True if running under GitHub Actions"""
    return os.getenv("GITHUB_ACTIONS")


def _get_preferred_database_name():
    if is_running_in_github_actions():
        if not os.getenv("PGDATABASE") and os.getenv("TOX_ENV_NAME"):
            # Generate an appropriately unique database name for this test run
            return "{prefix}_{suffix}".format(
                prefix=os.getenv("GITHUB_RUN_ID", "tox"),
                suffix=os.getenv("TOX_ENV_NAME").replace("-", "_"),
            )
    return "nav"


@pytest.fixture(scope='session')
def postgresql(request):
    """Fixture for all tests that depend on a running PostgreSQL server. This fixture
    will try to detect and use an existing PostgreSQL instance (like if running in a
    GitHub action), otherwise it will set up a temporary PostgreSQL server for the test
    session."""
    if not is_running_in_github_actions():
        request.getfixturevalue("docker_services")

    dbname = _get_preferred_database_name()
    _update_db_conf_for_test_run(dbname)
    _populate_test_database(dbname)
    yield dbname
    print("postgres fixture is done")


def _update_db_conf_for_test_run(database_name):
    db_conf_path = os.path.join(os.getenv("BUILDDIR"), "etc/db.conf")

    pghost = os.getenv('PGHOST', 'localhost')
    pgport = os.getenv('PGPORT', '5432')
    pguser = os.getenv('PGUSER', 'nav')
    pgpassword = os.getenv('PGPASSWORD', 'nav')
    with open(db_conf_path, "w") as output:
        output.writelines(
            [
                f"dbhost={pghost}\n",
                f"dbport={pgport}\n",
                f"db_nav={database_name}\n",
                f"script_default={pguser}\n",
                f"userpw_{pguser}={pgpassword}\n",
                "\n",
            ]
        )
    return db_conf_path


@retry(Exception, tries=3, delay=2, backoff=2)
def _populate_test_database(database_name, admin_username, admin_password):
    # Init/sync db schema
    env = {
        'PGHOST': 'localhost',
        'PGUSER': 'nav',
        'PGDATABASE': database_name,
        'PGPORT': '5432',
        'PGPASSWORD': 'nav',
        'PATH': os.getenv("PATH"),
    }
    navsyncdb_path = os.path.join(os.getenv("BUILDDIR"), 'bin', 'navsyncdb')
    subprocess.check_call([navsyncdb_path], env=env)  # , '-c'], #, '--drop-database'],

    # reset password of NAV admin account if indicated by environment
    if admin_password:
        sql = f"UPDATE account SET password = {adminpassword!r} WHERE login={admin_username!r}"
        subprocess.check_call(["psql", "-c", sql, database_name])

    # Add generic test data set
    test_data_path = './tests/docker/scripts/test-data.sql'
    subprocess.check_call(["psql", "-f", test_data_path, database_name], env=env)


@pytest.fixture(scope='session')
def admin_username():
    return os.environ.get('ADMINUSERNAME', 'admin')


@pytest.fixture(scope='session')
def admin_password():
    return os.environ.get('ADMINPASSWORD', 'admin')


@pytest.fixture(scope='session')
def gunicorn(postgresql):
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
