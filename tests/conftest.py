"""Pytest config and fixtures for all test suites"""
import os
import subprocess

import pytest
from retry import retry
import requests


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
    session.

    If your test needs to write to the database, it should ask for the `db` fixture
    instead, as this ensures changes are rolled back when the test is done.  However,
    if your test makes db changes that need to be visible from another process, you
    must make your own data fixture to ensure the data is removed when the test is
    done.
    """
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
def _populate_test_database(database_name):
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
    adminpassword = os.getenv("ADMINPASSWORD")
    if adminpassword:
        sql = f"UPDATE account SET password = {adminpassword!r} WHERE login='admin'"
        subprocess.check_call(["psql", "-c", sql, database_name])

    # Add generic test data set
    test_data_path = './tests/docker/scripts/test-data.sql'
    subprocess.check_call(["psql", "-f", test_data_path, database_name], env=env)


@pytest.fixture(scope='session')
def gunicorn(postgresql):
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
    # Fire off an initial request to ensure the webserver is actually running
    response = requests.get("http://localhost:8000/")
    assert response.status_code == 200, response.content
    yield gunicorn
    gunicorn.terminate()


@pytest.fixture(scope='session')
def web_target_url():
    yield "http://localhost:8000/"


@pytest.fixture(scope='session')
def web_admin_username():
    yield "admin"


@pytest.fixture(scope='session')
def web_admin_password():
    yield "admin"
