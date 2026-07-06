import string
import random
import errno

import pytest
from mock import patch

from nav.daemon import daemonexit, daemonize, PidFileWriteError


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


class TestDaemonizeForkParentExit:
    """The two intermediate fork parents in daemonize() must terminate with
    os._exit(), never sys.exit(). Running the Python interpreter's shutdown
    (module teardown and garbage collection) in a fork parent finalizes
    libffi/ctypes callback closures that, on hosts forbidding
    writable-and-executable memory, live in memory shared across the fork --
    corrupting them for the surviving daemon and crashing it (issue #4066).
    """

    @pytest.mark.parametrize(
        "fork_results",
        [
            pytest.param([111], id="first_parent"),
            pytest.param([0, 222], id="second_parent"),
        ],
    )
    def test_when_a_fork_parent_then_daemonize_should_exit_via_os_exit(
        self, fork_results
    ):
        # fork_results drives os.fork(): [111] makes the first fork the parent;
        # [0, 222] makes the first fork the child and the second fork the parent.
        with (
            patch('nav.daemon.pidfile_path', return_value='pidfile'),
            patch('os.fork', side_effect=fork_results),
            patch('os.chdir'),
            patch('os.umask'),
            patch('os.setsid'),
            patch('sys.exit', side_effect=_SysExitReached) as sys_exit,
            patch('os._exit', side_effect=_OsExitReached) as os_exit,
        ):
            with pytest.raises(_OsExitReached):
                daemonize('pidfile')

        os_exit.assert_called_once_with(0)
        sys_exit.assert_not_called()


# Helper functions


class _OsExitReached(Exception):
    """Raised by a mocked os._exit() to halt daemonize() at the intended
    exit point (the real os._exit() never returns)."""


class _SysExitReached(Exception):
    """Raised by a mocked sys.exit(); reaching it means the buggy
    interpreter-shutdown exit path was taken instead of os._exit()."""


def random_filename():
    rand = ''.join(
        random.choice(string.ascii_uppercase + string.digits) for _ in range(12)
    )
    return '/tmp/non-existant-{}.pid'.format(rand)
