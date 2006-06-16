#! /usr/bin/env python
# -*- coding: ISO8859-1 -*-
#
# Copyright 2006 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

"""
The NAV SMS daemon (smsd)

smsd dispatches SMS messages from the database to users' phones with the help
of plugins using Gammu and a cell on the COM port, or free SMS services on the
web.

Usage: smsd [-h] [-c] [-d sec] [-t phone no.]

  -h, --help            Show this help text
  -c, --cancel          Cancel (mark as ignored) all unsent messages
  -d, --delay           Set delay (in seconds) between queue checks
  -t, --test            Send a test message to <phone no.>
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id$"

import atexit
import email
import grp
import getopt
import logging # requires Python >= 2.3
import logging.handlers # requires Python >= 2.3
import os
import pwd
import smtplib
import socket
import sys
import time

import nav.config
import nav.path
import nav.smsd.queuenavdb
import nav.smsd.dispatchgammu


### VARIABLES

delay = 5 # Change at run-time with --delay
username = 'navcron'

# Daemonizing
pidfile = nav.path.localstatedir + '/run/smsd.py.pid'

# Logging
logfile = nav.path.localstatedir + '/log/smsd.py.log'
loglevel = logging.DEBUG
mailwarnlevel = logging.ERROR
mailserver = 'localhost'
mailaddr = nav.config.readConfig('nav.conf')['ADMIN_MAIL']
mailaddr = 'stein.magnus@jodal.no' # for devel


### MAIN FUNCTION

def main(args):
    # Initialize logger
    global logger
    logger = loginit('nav.smsd', logfile, loglevel, mailaddr, mailserver,
     mailwarnlevel)
    logger.info("smsd started.")

    # Get command line arguments
    optcancel = False
    opttest = False
    try:
        opts, args = getopt.getopt(args, 'hcd:t:',
         ['help', 'cancel', 'delay=', 'test='])
    except getopt.GetoptError, error:
        print >> sys.stderr, "%s\nTry `%s --help' for more information." % \
         (error, sys.argv[0])
        sys.exit(1)
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        if opt in ('-c', '--cancel'):
            optcancel = True
        if opt in ('-d', '--delay'):
            setdelay(val)
        if opt in ('-t', '--test'):
            opttest = True

    # Switch user to navcron
    switchuser(username)

    # Check if already running
    justme(pidfile)

    # Initialize dispatcher
    dispatcher = nav.smsd.dispatchgammu.dispatchgammu()

    # Send test message (in other words: test the dispatcher)
    if opttest:
        # FIXME: Format SMS
        # FIXME: Send SMS
        print "'--test' not implemented"
        sys.exit(0)

    # Initialize queue
    queue = nav.smsd.queuenavdb.queuenavdb()

    # Ignore unsent messages
    if optcancel:
        # FIXME: Ask queue to ignore unsent messages
        print "'--cancel' not implemented"
        sys.exit(0)

    # Daemonize
    daemonize(pidfile)

    # Loop forever
    while True:
        # FIXME: Implement queue and dispatcher
        
        # Queue: Get users with unsent messages

        # Loop over cell numbers
            # Queue: Get unsent messages for a user ordered by severity desc

            # Which dispatcher do we want to use? Depends on profile.
            # Dispatcher: Format SMS
            # Dispatcher: Send SMS
            # If success
                # Queue: Mark as sent/ignored
                # Log info
            # Else
                # Log error

        # Sleep a bit before the next run
        time.sleep(delay)

        # FIXME: Devel only
        break

    # Exit nicely
    sys.exit(0)


### INIT FUNCTIONS

def loginit(logname, logfile, loglevel, mailaddr, mailserver, mailwarnlevel):
    """
    Initalize the logging engine.

    Logs are delivered to three channels: logfile, stderr and mail.
    The two first are always tried when importance >= loglevel, while mail is
    always sent when importance >= mailwarnlevel.
    """

    fileformat = '%(asctime)s %(process)d %(levelname)s %(message)s'
    stderrformat = '%(levelname)s %(message)s'
    mailformat = '%(asctime)s %(process)d %(levelname)s %(message)s'

    try:
        filehandler = logging.FileHandler(logfile, 'a')
    except IOError, error:
        print >> sys.stderr, \
         "Failed creating file loghandler. Exiting. (%s)" % error
        sys.exit(error.errno)
    fileformatter = logging.Formatter(fileformat)
    filehandler.setFormatter(fileformatter)
    filehandler.setLevel(loglevel)
    
    try:
        stderrhandler = logging.StreamHandler(sys.stderr)
    except IOError, error:
        print >> sys.stderr, \
         "Failed creating stderr loghandler. Exiting. (%s)" % error
        sys.exit(error.errno)
    stderrformatter = logging.Formatter(stderrformat)
    stderrhandler.setFormatter(stderrformatter)
    stderrhandler.setLevel(loglevel)

    localuser = pwd.getpwuid(os.getuid())[0] 
    hostname = socket.gethostname()
    fromaddr = localuser + '@' + hostname
    try:
        mailhandler = logging.handlers.SMTPHandler(mailserver, fromaddr,
         mailaddr, 'NAV smsd warning from ' + hostname)
    except Exception, error:
        print >> sys.stderr, \
         "Failed creating SMTP loghandler. Exiting. (%s)" % error
        sys.exit(error.errno)
    mailformatter = logging.Formatter(mailformat)
    mailhandler.setFormatter(mailformatter)
    mailhandler.setLevel(mailwarnlevel)

    # Configure the root logger
    logger = logging.getLogger()
    logger.addHandler(filehandler)
    logger.addHandler(stderrhandler)
    logger.addHandler(mailhandler)

    # Return the $logname logger for our own logging
    logger = logging.getLogger(logname)
    logger.setLevel(1) # Let all info through to the root node
    return logger

def switchuser(username):
    """
    Switch user the process is running as to given username, normally 'navcron'.

    Will only work if we are running as root.

    Pseudo code:
    If navcron user exists
        Change user to navcron
        Change groups to navcron's groups
        If failed
            Die "unable to change uid/gids"
    Else
        Error
    """

    olduid = os.getuid()
    oldgid = os.getgid()

    try:
        name, passwd, uid, gid, gecos, dir, shell = pwd.getpwnam(username)
    except KeyError, error:
        logger.warning("User %s not found. Running as root! (%s)",
         username, error)
    else:
        if olduid != uid:
            try:
                # Set primary group
                os.setgid(gid)

                # Set non-primary groups
                gids = []
                for (name, passwd, gid, members) in grp.getgrall():
                    if username in members:
                        gids.append(gid)
                if len(gids) > 0:
                    os.setgroups(gids)

                # Set user id
                os.setuid(uid)
            except OSError, error:
                logger.error("Failed changing uid/gid from %d/%d to %d/%d. (%s)",
                 olduid, oldgid, uid, gid, error)
                sys.exit(error.errno)
            else:
                logger.info("uid/gid changed from %d/%d to %d/%d.",
                 olduid, oldgid, uid, gid)
        else:
            logger.info("Already running as uid/gid %d/%d.", olduid, oldgid)

def usage():
    """Print a usage screen to stderr."""
    print >> sys.stderr, __doc__

def setdelay(sec):
    """Set delay (in seconds) between queue checks."""
    global delay
    if sec.isdigit():
        sec = int(sec)
        delay = sec
        logger.info("Setting delay to %d seconds.", sec)
        return True
    else:
        logger.warning("Given delay not a digit. Using default.")
        return False


### DAEMON FUNCTIONS

def justme(pidfile):
    """
    Check if already running.

    Pseudo code:
    If pid file
        If corrupt pid file
            Die with error (which is caught by e.g. startstop.py)
        Get pid from file
        Send SIGNAL 0 to proccess with $pid
        If alive
            Bail out and die nicely
    Else
        Do nothing (in other words, the startup process continues)
    """

    if os.access(pidfile, os.R_OK):
        fd = file(pidfile, 'r')
        pid = fd.readline()
        fd.close()

        if pid.isdigit():
            pid = int(pid) 
        else:
            logger.error("Can't read pid from pid file %s. Bailing out.",
             pidfile)
            sys.exit(1)

        try:
            os.kill(pid, 0) # Sending signal 0 to check if process is alive
        except OSError, error:
            # Normally "No such process", and thus we continue
            return True
        else:
            # We assume the process lives and bails out
            logger.error("%s already running (pid %d), bailing out.",
             sys.argv[0], pid)
            sys.exit(1)
    else:
        # No pidfile, assume we're alone
        return True

def daemonize(pidfile, stdout = '/dev/null', stderr = None,
 stdin = '/dev/null'):
    """
    Move the process to the background as a daemon and write the pid of the
    daemon to the pidfile.

    Inspired by http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
    """

    # FIXME: When we require Python 2.4, replace '/dev/null' with
    # os.path.devnull in the default argument values above

    # Do first fork
    # (allow shell to return, and permit us to call setsid())
    try:
        pid = os.fork()
        if pid > 0:
            # We're the first parent. Exit!
            logger.info("First parent exiting. Second has pid %d.", pid)
            sys.exit(0)
    except OSError, error:
        logger.error("Fork #1 failed. Exiting. (%s)", error)
        sys.exit(error.errno)

    # Decouple from parent environment
    os.chdir('/') # In case the dir we started in are removed
    os.umask(0)
    os.setsid()

    # Do second fork
    # (prevent us from accidentally reacquiring a controlling terminal)
    try:
        pid = os.fork()
        if pid > 0:
            # We're the second parent. Exit!
            logger.info("Second parent exiting. Daemon has pid %d.", pid)
            sys.exit(0)
    except OSError, error:
        logger.error("Fork #2 failed. Exiting. (%s)", error)
        sys.exit(error.errno)

    # Now only the child is left :-)

    # Open file descriptors
    if not stderr:
        stderr = stdout
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    pid = os.getpid()
    logger.info("Daemon started with pid %d.", pid)

    # Write pidfile
    try:
        fd = file(pidfile, 'w+')
    except IOError, error:
        logger.error("Cannot open pidfile %s for writing. Exiting. (%s)",
         pidfile, error)
        sys.exit(error.errno)
    fd.write("%d\n" % pid)
    fd.close()

    # Set cleanup function to be run at exit so pidfile always is removed
    atexit.register(daemonexit, pidfile)
    
    # Close newfds before dup2-ing them
    sys.stdout.flush()
    sys.stderr.flush()
    os.close(sys.stdin.fileno())
    os.close(sys.stdout.fileno())
    os.close(sys.stderr.fileno())

    # Redirect standard file descriptors
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    return True

def daemonexit(pidfile):
    """
    Clean up after daemon process.

    Pseudo code:
    If pidfile
        Remove pidfile
    """

    logger.info("Daemon is exiting. Cleaning up...")
    try:
        os.remove(pidfile)
    except Exception, error:
        logger.error("Can't remove pidfile. Exiting. (%s)", error)
        # This will not start a loop, even if we're exiting from an exitfunc
        sys.exit(error.errno)
    logger.info("pidfile (%s) removed.", pidfile)


### BEGIN
main(sys.argv[1:])
