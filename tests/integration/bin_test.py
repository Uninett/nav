from subprocess import call
import pytest

def test_binary_runs(binary):
    retval = call(binary)
    assert retval == 0
