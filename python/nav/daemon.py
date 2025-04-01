# Copyright (C) 2006-2008, 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Help functions for daemonizing a process.

The normal usage sequence for the functions is:
    1. switchuser(username)
        Switch user the process is running as
    2. justme(pidfile)
        Check that the daemon is not already running
    3. daemonize(pidfile)
        Go into the background
        NOTE: Sets atexit function to daemonexit()
    4. daemonexit(pidfile)
        Clean up and delete the pidfile

All exceptions raised subclasses DaemonError.

"""

import atexit
import grp
import logging
import signal
import os
import errno
import pwd
import sys
import time
import nav.logs
from nav.config import NAV_CONFIG

nav.logs.set_log_config()
_logger = logging.getLogger('nav.daemon')


# Exception classes


class DaemonError(Exception):
    """Base class for all exceptions raised by nav.daemon."""

    pass


class UserNotFoundError(DaemonError):
    """Raised if requested user is not found and we have to run as root."""

    def __init__(self, username):
        super(UserNotFoundError, self).__init__()
        self.username = username

    def __str__(self):
        return "User (%s) not found, can't switch process user." % (self.username)


class SwitchUserError(DaemonError):
    """Raised if user switch failes, e.g. we don't have enough permissions."""

    def __init__(self, olduid, oldgid, newuid, newgid):
        super(SwitchUserError, self).__init__()
        self.olduid = olduid
        self.oldgid = oldgid
        self.newuid = newuid
        self.newgid = newgid

    def __str__(self):
        return "Failed to switch uid/gid from %d/%d to %d/%d." % (
            self.olduid,
            self.oldgid,
            self.newuid,
            self.newgid,
        )


class AlreadyRunningError(DaemonError):
    """Raised if the daemon is alrady running."""

    def __init__(self, pid):
        super(AlreadyRunningError, self).__init__()
        self.pid = pid

    def __str__(self):
        return "Daemon is already running with pid %d." % self.pid


class PidFileReadError(DaemonError):
    """Raised if we can't read a numeric pid from the pidfile."""

    def __init__(self, pidfile):
        super(PidFileReadError, self).__init__()
        self.pidfile = pidfile

    def __str__(self):
        return "Can't read pid from pidfile (%s)." % self.pidfile


class PidFileWriteError(DaemonError):
    """Raised if we can't write the pid to the pidfile."""

    def __init__(self, pidfile, error):
        super(PidFileWriteError, self).__init__()
        self.pidfile = pidfile
        self.error = error

    def __str__(self):
        return "Can't write pid to or remove pidfile (%s). (%s)" % (
            self.pidfile,
            self.error,
        )


class ForkError(DaemonError):
    """Raised if a fork fails."""

    def __init__(self, forkno, error):
        super(ForkError, self).__init__()
        self.forkno = forkno
        self.error = error

    def __str__(self):
        return "Failed fork #%d. (%s)" % (self.forkno, self.error)


# Daemon functions


def switchuser(username):
    """
    Switch user the process is running as.

    This method will only work if is are running as root.

    Arguments:
        ``username'' is the username of the user we want to run as.

    Returns/raises:
        If switch is a success, returns True.
        If user is unknown and we're still running as root, raises
        UserNotFoundError.
        If failing to switch, raises SwitchUserError.

    """

    # Get UID/GID we're running as
    olduid = os.getuid()
    oldgid = os.getgid()

    try:
        # Try to get information about the given username
        _name, _passwd, uid, gid, _gecos, _dir, _shell = pwd.getpwnam(username)
    except KeyError:
        raise UserNotFoundError(username)
    else:
        if olduid != uid:
            try:
                # Set primary group
                os.setgid(gid)

                # Set non-primary groups
                gids = []
                for _name, _passwd, gid, members in grp.getgrall():
                    if username in members:
                        gids.append(gid)
                if gids:
                    os.setgroups(gids)

                # Set user id
                os.setuid(uid)
            except OSError:
                # Failed changing uid/gid
                _logger.debug(
                    "Failed changing uid/gid from %d/%d to %d/%d.",
                    olduid,
                    oldgid,
                    uid,
                    gid,
                )
                raise SwitchUserError(olduid, oldgid, uid, gid)
            else:
                # Switch successful
                _logger.debug(
                    "uid/gid changed from %d/%d to %d/%d.", olduid, oldgid, uid, gid
                )
                return True
        else:
            # Already running as the given user
            _logger.debug("Running as uid/gid %d/%d.", olduid, oldgid)
            return True


def justme(pidfile):
    """
    Check if already running.

    Arguments:
        ``pidfile'' is the path to the process' pidfile.

    Returns/raises:
        If daemon is not running, returns True.
        If daemon is already running, raises AlreadyRunningError.
        If pidfile is unreadable, raises PidFileReadError.
        If pidfile is empty, but unremovable, raises PidFileWriteError.

    """
    pidfile = pidfile_path(pidfile)

    # If pidfile exists (is readable)
    if os.access(pidfile, os.R_OK):
        with open(pidfile, 'r') as pid_fd:
            pid = pid_fd.readline().strip()

        # Check if pidfile is empty (obscure, but we should handle it)
        if pid == '':
            # Remove pidfile and assume we're alone
            try:
                os.remove(pidfile)
            except OSError as error:
                _logger.debug("Unable to remove empty pidfile: %s", error)
                raise PidFileWriteError(pidfile, error)
            return True

        # Check if pid is readable
        if pid.isdigit():
            pid = int(pid)
        else:
            _logger.debug("Can't read pid from pid file %s.", pidfile)
            raise PidFileReadError(pidfile)

        try:
            # Sending signal 0 to check if process is alive
            os.kill(pid, 0)
        except OSError:
            # Normally this means "No such process", and thus we're alone
            return True
        else:
            # We assume the process lives and bails out
            _logger.debug("%s already running with pid %d.", sys.argv[0], pid)
            raise AlreadyRunningError(pid)
    else:
        # No pidfile, assume we're alone
        return True


def writepidfile(pidfile):
    """
    Creates or overwrites pidfile with the current process id.
    """
    # Write pidfile
    pidfile = pidfile_path(pidfile)
    pid = os.getpid()
    try:
        pid_fd = open(pidfile, 'w+')
    except IOError as error:
        _logger.debug(
            'Cannot open pidfile %s for writing. Exiting. (%s)', pidfile, error
        )
        raise PidFileWriteError(pidfile, error)

    pid_fd.write("%d\n" % pid)
    pid_fd.close()


def pidfile_path(pidfile):
    """Returns a fully qualified path for the given pidfile"""
    if pidfile.startswith(os.sep):
        return pidfile
    else:
        return os.path.join(NAV_CONFIG['PID_DIR'], pidfile)


def redirect_std_fds(stdin=None, stdout=None, stderr=None):
    """Close and redirect the standard file descriptors.

    If called without arguments, this function will first close, then
    redirect the low-level file descriptors of stdout, stderr and
    stdin to /dev/null.  If you wish to redirect one or more of these
    standard channels to an existing file, pass already open file
    objects as arguments.

    Arguments:
        ``stdin``  file object to redirect stdin to
        ``stdout`` file object to redirect stdout to
        ``stderr`` file object to redirect stderr to
    """
    if stdin is None:
        stdin = open(os.path.devnull, 'r')
    if stdout is None:
        stdout = open(os.path.devnull, 'w')
    if stderr is None:
        stderr = open(os.path.devnull, 'w')

    # Make sure to flush and close before redirecting
    sys.stdout.flush()
    sys.stderr.flush()
    os.close(sys.stdin.fileno())
    os.close(sys.stdout.fileno())
    os.close(sys.stderr.fileno())

    # Duplicate the file descriptors
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())


def daemonize(pidfile, stdin=None, stdout=None, stderr=None):
    """
    Move the process to the background as a daemon and write the pid of the
    daemon to the pidfile.

    Inspired by
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012

    Arguments:
        ``pidfile'' is the path to the process' pidfile.
        ``stdin``  file object to redirect stdin to (default: /dev/null)
        ``stdout`` file object to redirect stdout to (default: /dev/null)
        ``stderr`` file object to redirect stderr to (default: /dev/null)

    Returns/raises:
        If success, returns True.
        If fork fails, raises ForkError.
        If writing of pidfile fails, raises PidFileWriteError.

    """
    pidfile = pidfile_path(pidfile)
    # Do first fork
    # (allow shell to return, and permit us to call setsid())
    try:
        pid = os.fork()
        if pid > 0:
            # We're the first parent. Exit!
            _logger.debug("First parent exiting. Second has pid %d.", pid)
            sys.exit(0)
    except OSError as error:
        _logger.debug("Fork #1 failed. (%s)", error)
        raise ForkError(1, error)

    # Decouple from parent environment
    os.chdir('/')  # In case the dir we started in are removed
    os.umask(0)
    os.setsid()

    # Do second fork
    # (prevent us from accidentally reacquiring a controlling terminal)
    try:
        pid = os.fork()
        if pid > 0:
            # We're the second parent. Exit!
            _logger.debug("Second parent exiting. Daemon has pid %d.", pid)
            sys.exit(0)
    except OSError as error:
        _logger.exception("Fork #2 failed. (%s)", error)
        raise ForkError(2, error)

    # Now only the child is left :-)
    pid = os.getpid()
    _logger.debug("Daemon started with pid %d.", pid)

    writepidfile(pidfile)

    # Set cleanup function to be run at exit so pidfile always is removed
    atexit.register(daemonexit, pidfile)

    # Close and redirect standard file descriptors
    redirect_std_fds(stdin, stdout, stderr)

    return True


def daemonexit(pidfile):
    """
    Clean up after daemon process. This functions is only runned by the
    atexit handler.

    Arguments:
        ``pidfile'' is the path to the process' pidfile.

    Returns/raises:
        If success, returns True.
        If removal of pidfile fails, raises PidFileWriteError.

    """
    pidfile = pidfile_path(pidfile)
    _logger.debug("Daemon is exiting. Cleaning up...")

    try:
        os.remove(pidfile)
    except OSError as error:
        _logger.debug("Can't remove pidfile (%s). (%s)", pidfile, error)
        if error.errno != errno.ENOENT:
            raise PidFileWriteError(pidfile, error)
    else:
        _logger.debug("pidfile (%s) removed.", pidfile)
    return True


def safesleep(delay):
    """Hackish workaround to protect against Linux kernel bug in time.sleep().

    The bug will sometimes cause a call to time.sleep(1) to raise an
    exception.  If a daemon doesn't handle this exception, it will
    likely die.  Replacing calls to time.sleep(), where the argument
    could possibly become the value 1, with this function in daemon
    programs makes sure this exception is ignored if caught.

    See http://www.tummy.com/journals/entries/jafo_20070110_154659
    and https://bugs.launchpad.net/nav/+bug/352316
    and https://github.com/Uninett/nav/issues/462

    """
    try:
        time.sleep(delay)
    except IOError as error:
        if error.errno == 514:
            _logger.exception(
                "Ignoring possible Linux kernel bug in "
                "time.sleep(): IOError=514. See LP#352316"
            )
        else:
            raise


def signame(signum):
    """Looks up signal name from signal number"""
    lookup = dict(
        (num, name) for name, num in vars(signal).items() if name.startswith('SIG')
    )
    return lookup.get(signum, signum)
