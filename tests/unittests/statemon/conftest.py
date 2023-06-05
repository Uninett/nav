import os
import pytest


@pytest.fixture
def modulo_pid():
    """Returns this process' PID number, modulo 2^16. Because that's what pping uses
    to produce ping packet IDs
    """
    yield os.getpid() % 2**16
