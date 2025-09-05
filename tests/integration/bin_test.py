from shutil import which
import subprocess
import sys

import pytest


BINDIR = './python/nav/bin'


def test_script_runs(script):
    """Verifies that a script defined in pyproject.toml runs with a zero exit code"""
    if "netbiostracker" in script[0] and not which("nbtscan"):
        pytest.skip("nbtscan is not installed")

    proc = subprocess.Popen(script, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    (done, fail) = proc.communicate()
    retcode = proc.wait()

    print(done.decode('utf-8'))

    assert retcode == 0


@pytest.mark.timeout(20)
def test_naventity_runs_without_error_with_arguments(localhost, snmpsim):
    """
    Verifies that naventity runs with a zero exit code when given an
    ip address and a port

    Added in regards to: https://github.com/Uninett/nav/issues/2433
    """
    params = [BINDIR + "/naventity.py", localhost.ip, "-p", "1024"]
    if sys.version_info[0:2] == (3, 12):  # Python 3.12 is weird
        params += ["-t", "5.0"]
    proc = subprocess.Popen(
        params,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )
    (done, fail) = proc.communicate()
    retcode = proc.wait()

    if done:
        print(done.decode('utf-8'))
    if fail:
        print(fail.decode('utf-8'))

    assert retcode == 0


def test_nav_runs_without_error_without_arguments():
    """
    Verifies that nav runs with a zero exit code when given no arguments

    Added in regards to: https://github.com/Uninett/nav/issues/2601
    """
    proc = subprocess.Popen(
        [BINDIR + "/navmain.py"],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
    )
    (done, fail) = proc.communicate()
    retcode = proc.wait()

    if done:
        print(done.decode('utf-8'))
    if fail:
        print(fail.decode('utf-8'))

    assert retcode == 0
