"""Pytest config and fixtures for all test suites"""

import os
import platform
import subprocess
import psycopg2

import pytest
import requests
from requests.adapters import HTTPAdapter, Retry

from django.core.management import call_command
from django.test import override_settings


def pytest_configure(config):
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


def _is_postgresql_available():
    """Check if PostgreSQL is available and test user has database creation
    privileges"""
    try:
        conn_params = {
            'host': os.getenv('PGHOST', 'localhost'),
            'port': os.getenv('PGPORT', '5432'),
            'user': os.getenv('PGUSER', 'nav'),
            'password': os.getenv('PGPASSWORD', 'nav'),
            'dbname': 'postgres',  # Connect to default postgres db to test connection
        }
        conn = psycopg2.connect(**conn_params)

        # Test if user can create databases
        cursor = conn.cursor()
        cursor.execute(
            "SELECT has_database_privilege(%s, 'CREATE')", (conn_params['user'],)
        )
        can_create_db = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return can_create_db
    except (psycopg2.OperationalError, psycopg2.Error):
        return False


def _get_preferred_database_name():
    if is_running_in_github_actions():
        if not os.getenv("PGDATABASE") and os.getenv("TOX_ENV_NAME"):
            # Generate an appropriately unique database name for this test run
            return "{prefix}_{suffix}".format(
                prefix=os.getenv("GITHUB_RUN_ID", "tox"),
                suffix=os.getenv("TOX_ENV_NAME").replace("-", "_"),
            )
    return "test_nav"


@pytest.fixture(scope='session')
def postgresql(request, configuration_dir, admin_username, admin_password):
    """Fixture for all tests that depend on a running PostgreSQL server.

    This fixture assumes PostgreSQL is already available (e.g., via devcontainer or
    docker-compose). If PostgreSQL is not available, tests requiring this fixture
    will be skipped.

    If your test needs to write to the database, it should ask for the `db` fixture
    instead, as this ensures changes are rolled back when the test is done.  However,
    if your test makes db changes that need to be visible from another process, you
    must make your own data fixture to ensure the data is removed when the test is
    done.
    """
    # Check if PostgreSQL is available
    if not _is_postgresql_available():
        pytest.skip("PostgreSQL is not available")

    dbname = _get_preferred_database_name()
    print("Using test database name:", dbname)
    _update_db_conf_for_test_run(configuration_dir, dbname)
    _populate_test_database(dbname, admin_username, admin_password)
    yield dbname
    print("postgresql fixture is done")


def _update_db_conf_for_test_run(config_dir, database_name):
    """Update db.conf in the configuration directory with test database settings"""
    db_conf_path = config_dir / "db.conf"

    pghost = os.getenv('PGHOST', 'localhost')
    pgport = os.getenv('PGPORT', '5432')
    pguser = os.getenv('PGUSER', 'nav')
    pgpassword = os.getenv('PGPASSWORD', 'nav')
    with open(str(db_conf_path), "w") as output:
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


def _populate_test_database(database_name, admin_username, admin_password):
    # Init/sync db schema
    env = {
        'PGHOST': os.getenv("PGHOST", 'localhost'),
        'PGUSER': os.getenv("PGUSER", 'nav'),
        'PGDATABASE': database_name,
        'PGPORT': os.getenv("PGPORT", '5432'),
        'PGPASSWORD': os.getenv("PGPASSWORD", 'nav'),
        'PATH': os.getenv("PATH"),
        'NAV_CONFIG_DIR': os.getenv(
            "NAV_CONFIG_DIR"
        ),  # Pass config dir to subprocesses
    }
    # Run navsyncdb as Python module instead of relying on BUILDDIR/bin
    subprocess.check_call(
        [
            'python',
            '-m',
            'nav.pgsync',
            '--drop-database',
            '--create',
        ],
        env=env,
    )

    # reset password of NAV admin account if indicated by environment
    if admin_password:
        sql = (
            f"UPDATE account SET password = {admin_password!r} "
            f"WHERE login={admin_username!r}"
        )
        subprocess.check_call(["psql", "-c", sql], env=env)

    # Add generic test data set
    # Use absolute path relative to this conftest.py file
    conftest_dir = os.path.dirname(os.path.abspath(__file__))
    test_data_path = os.path.join(conftest_dir, 'docker', 'scripts', 'test-data.sql')
    subprocess.check_call(["psql", "-f", test_data_path], env=env)


@pytest.fixture(scope='session')
def configuration_dir(tmp_path_factory):
    """Creates a temporary NAV configuration directory with example config files"""
    config_dir = tmp_path_factory.mktemp("nav_config")

    # Set NAV_CONFIG_DIR to point to our temporary config directory
    old_config_dir = os.environ.get('NAV_CONFIG_DIR')
    os.environ['NAV_CONFIG_DIR'] = str(config_dir)

    # Install default config files using nav.config functionality
    from nav.config import install_example_config_files

    install_example_config_files(str(config_dir))

    # Apply integration test specific configuration changes
    _configure_for_integration_tests(config_dir)

    yield config_dir

    # Restore original NAV_CONFIG_DIR
    if old_config_dir is not None:
        os.environ['NAV_CONFIG_DIR'] = old_config_dir
    else:
        os.environ.pop('NAV_CONFIG_DIR', None)


def _configure_for_integration_tests(config_dir):
    """Apply integration test specific configuration changes"""
    import re

    # Configure nav.conf for integration tests
    nav_conf_path = config_dir / "nav.conf"
    if nav_conf_path.exists():
        with open(nav_conf_path, 'r') as f:
            content = f.read()

        # Enable Django debug mode
        content = re.sub(
            r'^#?DJANGO_DEBUG.*', 'DJANGO_DEBUG=True', content, flags=re.MULTILINE
        )

        # Set NAV_USER to current user
        current_user = os.getenv('USER', 'nav')
        content = re.sub(
            r'^NAV_USER.*', f'NAV_USER={current_user}', content, flags=re.MULTILINE
        )

        # Set upload directory to temp dir
        uploads_dir = config_dir / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        content = re.sub(
            r'^#?UPLOAD_DIR.*', f'UPLOAD_DIR={uploads_dir}', content, flags=re.MULTILINE
        )

        with open(nav_conf_path, 'w') as f:
            f.write(content)

    # Configure graphite.conf for integration tests
    graphite_conf_path = config_dir / "graphite.conf"
    if graphite_conf_path.exists():
        with open(graphite_conf_path, 'r') as f:
            content = f.read()

        # Set graphite base URL
        content = re.sub(
            r'^#?base.*', 'base=http://localhost:9000', content, flags=re.MULTILINE
        )

        with open(graphite_conf_path, 'w') as f:
            f.write(content)

    # Configure logging.conf for integration tests
    logging_conf_path = config_dir / "logging.conf"
    if logging_conf_path.exists():
        import configparser

        config = configparser.ConfigParser()
        config.read(str(logging_conf_path))

        # Ensure [levels] section exists
        if not config.has_section('levels'):
            config.add_section('levels')

        # Add debug logging for nav.eventengine
        config.set('levels', 'nav.eventengine', 'DEBUG')

        with open(str(logging_conf_path), 'w') as f:
            config.write(f)


@pytest.fixture(scope='session')
def admin_username():
    return os.environ.get('ADMINUSERNAME', 'admin')


@pytest.fixture(scope='session')
def admin_password():
    return os.environ.get('ADMINPASSWORD', 'admin')


@pytest.fixture(scope='session')
def build_sass():
    """Builds the NAV SASS files into CSS files that can be installed as static files"""
    subprocess.check_call(["make", "sassbuild"])


@pytest.fixture(scope='session')
def staticfiles(build_sass, tmp_path_factory):
    """Collects Django static files into a temporary directory and return the web root
    directory path that can be served by a web server.
    """
    webroot = tmp_path_factory.mktemp("webroot")
    static = webroot / "static"
    with override_settings(STATIC_ROOT=static):
        print(f"Collecting static files in {static!r}")
        call_command('collectstatic', interactive=False)
        yield webroot


@pytest.fixture(scope='session')
def gunicorn(postgresql, staticfiles):
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
            f'navtest_wsgi:nav_test_app(root={str(staticfiles)!r})',
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
