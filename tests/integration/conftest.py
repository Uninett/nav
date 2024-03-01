from __future__ import print_function
import os
import io
import re
import shlex
from itertools import cycle
from shutil import which
import subprocess
import time

import pytest
from django.test import Client

gunicorn = None

########################################################################
#                                                                      #
# Set up the required components for an integration test. Components   #
# such as PostgreSQL and Apache are assumed to already be installed on #
# the system. The system is assumed to be Debian. See                  #
# tests/docker/Dockerfile.                                             #
#                                                                      #
########################################################################

if os.environ.get('WORKSPACE'):
    SCRIPT_PATH = os.path.join(os.environ['WORKSPACE'], 'tests/docker/scripts')
else:
    SCRIPT_PATH = '/'
SCRIPT_CREATE_DB = os.path.join(SCRIPT_PATH, 'create-db.sh')


def pytest_configure(config):
    subprocess.check_call([SCRIPT_CREATE_DB])
    os.environ['TARGETURL'] = "http://localhost:8000/"
    start_gunicorn()

    # Bootstrap Django config
    from nav.bootstrap import bootstrap_django

    bootstrap_django('pytest')

    # Install custom reactor for Twisted tests
    from nav.ipdevpoll.epollreactor2 import install

    install()

    # Setup test environment for Django
    from django.test.utils import setup_test_environment

    setup_test_environment()


def pytest_unconfigure(config):
    stop_gunicorn()


def start_gunicorn():
    global gunicorn
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


def stop_gunicorn():
    if gunicorn:
        gunicorn.terminate()


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
    if 'binary' in metafunc.fixturenames:
        binaries = _nav_binary_tests()
        ids = [b[0] for b in binaries]
        metafunc.parametrize("binary", _nav_binary_tests(), ids=ids)
    elif 'admin_navlet' in metafunc.fixturenames:
        from nav.models.profiles import AccountNavlet

        navlets = AccountNavlet.objects.filter(account__login='admin')
        metafunc.parametrize("admin_navlet", navlets)


def _nav_binary_tests():
    for binary in _nav_binary_list():
        for args in _scan_testargs(binary):
            if args:
                yield args


def _nav_binary_list():
    files = sorted(
        os.path.join(BINDIR, f) for f in os.listdir(BINDIR) if not _is_excluded(f)
    )
    return (f for f in files if os.path.isfile(f))


def _is_excluded(filename):
    return (
        filename.endswith('~')
        or filename.startswith('.')
        or filename.startswith('__')
        or filename.startswith('Makefile')
    )


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
def token():
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
    snmpsimd = which('snmpsimd.py')
    assert snmpsimd, "Could not find snmpsimd.py"
    workspace = os.getenv('WORKSPACE', os.getenv('HOME', '/source'))
    proc = subprocess.Popen(
        [
            snmpsimd,
            '--data-dir={}/tests/integration/snmp_fixtures'.format(workspace),
            '--log-level=error',
            '--agent-udpv4-endpoint=127.0.0.1:1024',
        ],
        env={'HOME': workspace},
    )

    while not _lookfor('0100007F:0400', '/proc/net/udp'):
        print("Still waiting for snmpsimd to listen for queries")
        proc.poll()
        time.sleep(0.1)

    yield
    proc.kill()


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


@pytest.fixture(scope='session')
def admin_username():
    return os.environ.get('ADMINUSERNAME', 'admin')


@pytest.fixture(scope='session')
def admin_password():
    return os.environ.get('ADMINPASSWORD', 'admin')
