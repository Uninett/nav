import string
import random
import errno

import pytest
from mock import patch

from nav.daemon import daemonexit, PidFileWriteError


def test_daemonexit_should_pass_on_unexpected_exceptions():
    with patch('os.remove') as os_remove:
        expected = Exception("Bull")
        os_remove.side_effect = expected
        with pytest.raises(Exception) as error:
            daemonexit('/tmp/foobar.pid')

        assert error.value is expected


def test_daemonexit_should_ignore_nonexistent_pidfile():
    assert daemonexit(random_filename())


def test_daemonexit_should_raise_pidfilewriteerror_on_other_os_errors():
    with patch('os.remove') as os_remove:
        os_remove.side_effect = OSError(errno.EPERM, "Access denied")

        with pytest.raises(PidFileWriteError):
            daemonexit(random_filename())


# Helper functions

def random_filename():
    rand = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits
        )
        for _ in range(12)
    )
    return '/tmp/non-existant-{}.pid'.format(rand)
