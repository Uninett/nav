import os
import io
import re
import shlex

import pytest
from django.test import Client

from nav.buildconf import bindir
from nav.models.manage import Netbox

TESTARGS_PATTERN = re.compile(
    r'^# +-\*-\s*testargs:\s*(?P<args>.*?)\s*(-\*-)?\s*$',
    re.MULTILINE)
NOTEST_PATTERN = re.compile(
    r'^# +-\*-\s*notest\s*(-\*-)?\s*$', re.MULTILINE)


def pytest_generate_tests(metafunc):
    if 'binary' in metafunc.fixturenames:
        binaries = _nav_binary_tests()
        ids = [b[0] for b in binaries]
        metafunc.parametrize("binary", _nav_binary_tests(), ids=ids)


def _nav_binary_tests():
    for binary in _nav_binary_list():
        for args in _scan_testargs(binary):
            if args:
                yield args


def _nav_binary_list():
    files = sorted(os.path.join(bindir, f)
                   for f in os.listdir(bindir)
                   if not _is_excluded(f))
    return (f for f in files if os.path.isfile(f))


def _is_excluded(filename):
    return (filename.endswith('~') or filename.startswith('.') or
            filename.startswith('Makefile'))


def _scan_testargs(filename):
    """
    Scans filename for testargs comments and returns a list of elements
    suitable for invocation of this binary with the given testargs
    """
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


@pytest.fixture()
def localhost():
    box = Netbox(ip='127.0.0.1', sysname='localhost.example.org',
                 organization_id='myorg', room_id='myroom', category_id='SRV',
                 read_only='public', snmp_version=2)
    box.save()
    yield box
    print("teardown test device")
    box.delete()


@pytest.fixture(scope='session')
def client():
    """Provides a Django test Client object already logged in to the web UI as
    an admin"""
    from django.core.urlresolvers import reverse

    client_ = Client()
    url = reverse('webfront-login')
    username = os.environ.get('ADMINUSERNAME', 'admin')
    password = os.environ.get('ADMINPASSWORD', 'admin')
    client_.post(url, {'username': username,
                       'password': password})
    return client_
