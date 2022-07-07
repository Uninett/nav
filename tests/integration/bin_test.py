import pytest
import sys
import subprocess


def test_binary_runs(binary):
    """Verifies that a command runs with a zero exit code"""
    proc = subprocess.Popen(binary, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    (done, fail) = proc.communicate()
    retcode = proc.wait()

    print(done.decode('utf-8'))

    assert retcode == 0


@pytest.mark.timeout(10)
def test_naventity_runs_without_error_with_arguments(localhost, snmpsim):
    """
    Verifies that naventity runs with a zero exit code when given an
    ip address and a port

    Added in regards to: https://github.com/Uninett/nav/issues/2433
    """
    proc = subprocess.Popen(
        ["./bin/naventity", localhost.ip, "-p", "1024"],
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
