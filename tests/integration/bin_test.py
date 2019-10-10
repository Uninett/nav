import sys
import subprocess


def test_binary_runs(binary):
    """Verifies that a command runs with a zero exit code"""
    proc = subprocess.Popen(binary, stderr=subprocess.STDOUT,
                            stdout=subprocess.PIPE)
    (done, fail) = proc.communicate()
    retcode = proc.wait()

    print(done.decode('utf-8'))

    assert retcode == 0
