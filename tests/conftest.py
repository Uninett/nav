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


@pytest.fixture(scope="session")
def rsa_private_key() -> str:
    """Yields a private key in PEM format"""
    key = """-----BEGIN PRIVATE KEY-----
MIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQCp+4AEZM4uYZKu
/hrKzySMTFFx3/ncWo6XAFpADQHXLOwRB9Xh1/OwigHiqs/wHRAAmnrlkwCCQA8r
xiHBAMjp5ApbkyggQz/DVijrpSba6Tiy1cyBTZC3cvOK2FpJzsakJLhIXD1HaULO
ClyIJB/YrmHmQc8SL3Uzou5mMpdcBC2pzwmEW1cvQURpnvgrDF8V86GrQkjK6nIP
IEeuW6kbD5lWFAPfLf1ohDWex3yxeSFyXNRApJhbF4HrKFemPkOi7acsky38UomQ
jZgAMHPotJNkQvAHcnXHhg0FcWGdohv5bc/Ctt9GwZOzJxwyJLBBsSewbE310TZi
3oLU1TmvAgMBAAECgf8zrhi95+gdMeKRpwV+TnxOK5CXjqvo0vTcnr7Runf/c9On
WeUtRPr83E4LxuMcSGRqdTfoP0loUGb3EsYwZ+IDOnyWWvytfRoQdExSA2RM1PDo
GRiUN4Dy8CrGNqvnb3agG99Ay3Ura6q5T20n9ykM4qKL3yDrO9fmWyMgRJbAOAYm
xzf7H910mDZghXPpq8nzDky0JLNZcaqbxuPQ3+EI4p2dLNXbNqMPs8Y20JKLeOPs
HikRM0zfhHEJSt5IPFQ54/CzscGHGeCleQINWTgvDLMcE5fJMvbLLZixV+YsBfAq
e2JsSubS+9RI2ktMlSKaemr8yeoIpsXfAiJSHkECgYEA0NKU18xK+9w5IXfgNwI4
peu2tWgwyZSp5R2pdLT7O1dJoLYRoAmcXNePB0VXNARqGxTNypJ9zmMawNmf3YRS
BqG8aKz7qpATlx9OwYlk09fsS6MeVmaur8bHGHP6O+gt7Xg+zhiFPvU9P5LB+C0Z
0d4grEmIxNhJCtJRQOThD8ECgYEA0GKRO9SJdnhw1b6LPLd+o/AX7IEzQDHwdtfi
0h7hKHHGBlUMbIBwwjKmyKm6cSe0PYe96LqrVg+cVf84wbLZPAixhOjyplLznBzF
LqOrfFPfI5lQVhslE1H1CdLlk9eyT96jDgmLAg8EGSMV8aLGj++Gi2l/isujHlWF
BI4YpW8CgYEAsyKyhJzABmbYq5lGQmopZkxapCwJDiP1ypIzd+Z5TmKGytLlM8CK
3iocjEQzlm/jBfBGyWv5eD8UCDOoLEMCiqXcFn+uNJb79zvoN6ZBVGl6TzhTIhNb
73Y5/QQguZtnKrtoRSxLwcJnFE41D0zBRYOjy6gZJ6PSpPHeuiid2QECgYACuZc+
mgvmIbMQCHrXo2qjiCs364SZDU4gr7gGmWLGXZ6CTLBp5tASqgjmTNnkSumfeFvy
ZCaDbJbVxQ2f8s/GajKwEz/BDwqievnVH0zJxmr/kyyqw5Ybh5HVvA1GfqaVRssJ
DvTjZQDft0a9Lyy7ix1OS2XgkcMjTWj840LNPwKBgDPXMBgL5h41jd7jCsXzPhyr
V96RzQkPcKsoVvrCoNi8eoEYgRd9jwfiU12rlXv+fgVXrrfMoJBoYT6YtrxEJVdM
RAjRpnE8PMqCUA8Rd7RFK9Vp5Uo8RxTNvk9yPvDv1+lHHV7lEltIk5PXuKPHIrc1
nNUyhzvJs2Qba2L/huNC
-----END PRIVATE KEY-----"""
    return key


@pytest.fixture(scope="session")
def rsa_public_key() -> str:
    """Yields a public key in PEM format"""
    key = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqfuABGTOLmGSrv4ays8k
jExRcd/53FqOlwBaQA0B1yzsEQfV4dfzsIoB4qrP8B0QAJp65ZMAgkAPK8YhwQDI
6eQKW5MoIEM/w1Yo66Um2uk4stXMgU2Qt3LzithaSc7GpCS4SFw9R2lCzgpciCQf
2K5h5kHPEi91M6LuZjKXXAQtqc8JhFtXL0FEaZ74KwxfFfOhq0JIyupyDyBHrlup
Gw+ZVhQD3y39aIQ1nsd8sXkhclzUQKSYWxeB6yhXpj5Dou2nLJMt/FKJkI2YADBz
6LSTZELwB3J1x4YNBXFhnaIb+W3PwrbfRsGTsyccMiSwQbEnsGxN9dE2Yt6C1NU5
rwIDAQAB
-----END PUBLIC KEY-----"""
    return key
