import importlib.metadata
import importlib.util
import io
import os
import re
import shlex
import subprocess
import sys
import time
from itertools import cycle
from pathlib import Path
from shutil import which

import toml
import pytest
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.test import Client
from django.test.testcases import LiveServerThread


########################################################################
#                                                                      #
# Set up the required components for an integration test. PostgreSQL   #
# is assumed to already be available, with connection details in the   #
# PG* environment variables.  The connecting role must have CREATEDB   #
# privileges.                                                          #
#                                                                      #
########################################################################


def pytest_configure(config):
    from ..setup_test_config import ensure_config_dir, create_test_database

    ensure_config_dir()
    create_test_database()


@pytest.fixture(scope='session')
def live_server():
    """Start a threaded Django live server for integration tests."""
    server_thread = LiveServerThread('localhost', StaticFilesHandler, port=0)
    server_thread.daemon = True
    server_thread.start()
    server_thread.is_ready.wait()
    if server_thread.error:
        raise server_thread.error
    yield f'http://{server_thread.host}:{server_thread.port}'
    server_thread.terminate()
    server_thread.join()


########################################################################
#                                                                      #
# All to do with discovering all NAV binaries and building fixtures to #
# generate tests for each of them                                      #
#                                                                      #
########################################################################
TESTARGS_PATTERN = re.compile(
    r'^# +-\*-\s*testargs:\s*(?P<args>.*?)\s*(-\*-)?\s*$', re.MULTILINE
)
NOTEST_PATTERN = re.compile(r'^# +-\*-\s*notest\s*(-\*-)?\s*$', re.MULTILINE)
BINDIR = './python/nav/bin'


def pytest_generate_tests(metafunc):
    if 'script' in metafunc.fixturenames:
        scripts = _nav_script_tests()
        ids = [s[0] for s in scripts]
        metafunc.parametrize("script", _nav_script_tests(), ids=ids)
    elif 'admin_navlet' in metafunc.fixturenames:
        from nav.models.profiles import AccountNavlet

        navlets = AccountNavlet.objects.filter(account__login='admin')
        metafunc.parametrize("admin_navlet", navlets)


def _nav_script_tests():
    """Generates a list of command lines to run to test all the NAV scripts defined
    in pyproject.toml.

    Each NAV script can define 0 to many sets of test arguments that should be used
    when executing the script, using comments at the top of the file.  This is because
    some of the scripts are designed to require some arguments to be present in order
    to run without exiting with an error.
    """
    for script, module_name in _nav_scripts_map().items():
        spec = importlib.util.find_spec(module_name)
        for args in _scan_testargs(spec.origin):
            if args:
                yield [script] + args[1:]


def _nav_scripts_map() -> dict[str, str]:
    """Returns a map of installable script names to NAV module names from
    pyproject.toml.
    """
    data = toml.load('pyproject.toml')
    scripts: dict[str, str] = data.get('project', {}).get('scripts', {})
    return {
        script: module.split(':', maxsplit=1)[0]
        for script, module in scripts.items()
        if module.startswith('nav.')
    }


def _scan_testargs(filename):
    """
    Scans filename for testargs comments and returns a list of elements
    suitable for invocation of this binary with the given testargs
    """
    print("Getting test args from {}".format(filename))
    contents = io.open(filename, encoding="utf-8").read()
    matches = TESTARGS_PATTERN.findall(contents)
    if matches:
        retval = []
        for testargs, _ in matches:
            testargs = shlex.split(testargs)
            retval.append([filename] + testargs)
        return retval
    else:
        matches = NOTEST_PATTERN.search(contents)
        if not matches:
            return [[filename]]
        else:
            return []


##################
#                #
# Other fixtures #
#                #
##################


@pytest.fixture()
def management_profile():
    from nav.models.manage import ManagementProfile

    profile = ManagementProfile(
        name="Test connection profile",
        protocol=ManagementProfile.PROTOCOL_SNMP,
        configuration={
            "version": 2,
            "community": "public",
            "write": False,
        },
    )
    profile.save()
    yield profile
    profile.delete()


@pytest.fixture()
def localhost(management_profile):
    from nav.models.manage import Netbox, NetboxProfile

    box = Netbox(
        ip='127.0.0.1',
        sysname='localhost.example.org',
        organization_id='myorg',
        room_id='myroom',
        category_id='SRV',
    )
    box.save()
    NetboxProfile(netbox=box, profile=management_profile).save()
    yield box
    print("teardown test device")
    box.delete()


@pytest.fixture()
def netbox_type(localhost):
    from nav.models.manage import NetboxType, Vendor

    vendor = Vendor(id="testvendor")
    vendor.save()
    netbox_type = NetboxType(
        description='Test device type',
        vendor=vendor,
        name='testtype',
    )
    netbox_type.save()
    yield netbox_type
    netbox_type.delete()
    vendor.delete()


@pytest.fixture()
def localhost_using_legacy_db():
    """Alternative to the Django-based localhost fixture, for tests that operate on
    code that uses legacy database connections.
    """
    from nav.db import getConnection

    conn = getConnection('default')
    cursor = conn.cursor()

    sql = """
    INSERT INTO netbox
    (ip, sysname, orgid, roomid, catid)
    VALUES
    (%s, %s, %s, %s, %s)
    RETURNING netboxid;
    """
    cursor.execute(
        sql, ('127.0.0.1', 'localhost.example.org', 'myorg', 'myroom', 'SRV')
    )
    netboxid = cursor.fetchone()[0]
    conn.commit()
    yield netboxid

    print("teardown localhost device using legacy connection")
    cursor.execute("DELETE FROM netbox WHERE netboxid=%s", (netboxid,))
    conn.commit()


@pytest.fixture(scope='function')
def client(admin_username, admin_password):
    """Provides a Django test Client object already logged in to the web UI as
    an admin"""
    from django.urls import reverse

    client_ = Client()
    url = reverse('webfront-login')
    client_.post(url, {'username': admin_username, 'password': admin_password})
    return client_


@pytest.fixture(scope='function')
def db(request):
    """Ensures db modifications are rolled back after the test ends.

    This is done by disabling transaction management, running everything
    inside a transaction that is rolled back after the test is done.
    Effectively, it reuses the functionality of Django's own TestCase
    implementation, just fitted for pytest.

    This idea is entirely lifted from pytest-django; we can't use
    pytest-django directly, yet, because it won't work on Django 1.7 (and NAV
    has fairly non-standard use of Django, anyway)

    """
    if _is_django_unittest(request):
        return

    from nav.tests.cases import DjangoTransactionTestCase as django_case

    test_case = django_case(methodName='__init__')
    test_case._pre_setup()
    request.addfinalizer(test_case._post_teardown)


def _is_django_unittest(request_or_item):
    """Returns True if the request_or_item is a Django test case, otherwise
    False
    """
    from django.test import SimpleTestCase

    cls = getattr(request_or_item, 'cls', None)

    if cls is None:
        return False

    return issubclass(cls, SimpleTestCase)


@pytest.fixture(scope='function')
def token(db):
    """Creates a write enabled token for API access but without endpoints

    Tests should manipulate the endpoints as they see fit.
    """
    from nav.models.api import APIToken
    from datetime import datetime, timedelta

    token = APIToken(
        token='xxxxxx',
        expires=datetime.now() + timedelta(days=1),
        client_id=1,
        permission='write',
    )
    token.save()
    return token


@pytest.fixture(scope='function')
def api_client(token):
    """Creates a client for API access"""

    from rest_framework.test import APIClient

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Token ' + token.token)
    return client


@pytest.fixture(scope='session')
def snmpsim():
    """Sets up an external snmpsimd process so that SNMP communication can be simulated
    by the test that declares a dependency to this fixture. Data fixtures are loaded
    from the snmp_fixtures subdirectory.
    """
    workspace = str(Path(__file__).resolve().parent.parent.parent)
    command = _build_snmpsim_command(workspace)
    env = {**os.environ, 'HOME': workspace}
    proc = subprocess.Popen(command, env=env)

    while not _lookfor('0100007F:0400', '/proc/net/udp'):
        print("Still waiting for snmpsimd to listen for queries")
        if proc.poll() is not None:
            pytest.fail(
                f"snmpsim process exited prematurely (exit code {proc.returncode})"
            )
        time.sleep(0.1)

    yield
    proc.kill()


def _build_snmpsim_command(workspace):
    """Returns the command list to start snmpsim-command-responder.

    Prefers running via uvx in an isolated Python 3.11 environment to avoid a
    known performance regression in snmpsim on Python 3.13+
    (https://github.com/lextudio/pysnmp/issues/223).  Falls back to a locally
    installed snmpsim-command-responder if uvx is not available.
    """
    data_dir = f'{workspace}/tests/integration/snmp_fixtures'
    snmpsim_args = [
        f'--data-dir={data_dir}',
        '--log-level=error',
        '--agent-udpv4-endpoint=127.0.0.1:1024',
    ]

    if which('uvx') and _uv_has_python('3.11'):
        snmpsim_pkg = _installed_snmpsim_spec()
        return [
            'uvx',
            '--python=3.11',
            f'--from={snmpsim_pkg}',
            'snmpsim-command-responder',
        ] + snmpsim_args

    snmpsimd = which('snmpsim-command-responder')
    if not snmpsimd:
        pytest.skip("Neither uvx nor snmpsim-command-responder found")

    if sys.version_info >= (3, 13):
        import warnings

        warnings.warn(
            "Running snmpsim under Python 3.13+ without uvx. "
            "This is known to be extremely slow due to a dbm.sqlite3 "
            "performance regression "
            "(https://github.com/lextudio/pysnmp/issues/223). "
            "Expect many SNMP-dependent tests to fail with timeouts. "
            "Install uv to run snmpsim in an isolated Python 3.11 "
            "environment automatically.",
            stacklevel=1,
        )

    return [snmpsimd] + snmpsim_args


def _uv_has_python(version):
    """Returns True if uv can find the given Python version."""
    result = subprocess.run(
        ['uv', 'python', 'find', version],
        capture_output=True,
    )
    return result.returncode == 0


def _installed_snmpsim_spec():
    """Returns a pip specifier for the locally installed snmpsim version.

    Falls back to an unpinned 'snmpsim' if the package is not installed.
    """
    try:
        version = importlib.metadata.version('snmpsim')
        return f'snmpsim=={version}'
    except importlib.metadata.PackageNotFoundError:
        return 'snmpsim'


@pytest.fixture()
def snmp_agent_proxy(snmpsim, snmp_ports):
    """Returns an AgentProxy instance prepared to talk to localhost. The open() method
    has not been called, so its attributes can be changed before the socket is opened.
    """
    from nav.ipdevpoll.snmp import AgentProxy
    from nav.ipdevpoll.snmp.common import SNMPParameters

    port = next(snmp_ports)
    agent = AgentProxy(
        '127.0.0.1',
        1024,
        community='placeholder',
        snmpVersion='v2c',
        protocol=port.protocol,
        snmp_parameters=SNMPParameters(timeout=1, max_repetitions=5, throttle_delay=0),
    )
    return agent


_ports = None  # to store a cycling generator of snmp client ports


@pytest.fixture(scope='session')
def snmp_ports():
    """Returns a cyclic generator of snmpprotocol.port() to use for agent proxies"""
    from pynetsnmp.twistedsnmp import snmpprotocol

    global _ports

    if _ports is None:
        _ports = cycle(snmpprotocol.port() for i in range(50))
    return _ports


def _lookfor(string, filename):
    """Very simple grep-like function"""
    data = io.open(filename, 'r', encoding='utf-8').read()
    return string in data


@pytest.fixture
def admin_account(db):
    from nav.models.profiles import Account

    yield Account.objects.get(id=Account.ADMIN_ACCOUNT)


@pytest.fixture()
def non_admin_account(db):
    from nav.models.profiles import Account

    account = Account(login="other_user", name="Other User")
    account.set_password("password")
    account.save()
    yield account
    account.delete()
