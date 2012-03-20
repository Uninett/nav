#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2007, 2008, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
The NAV Alert Engine daemon (alertengine)

This background process polls the alert queue for new alerts from the
eventengine and sends put alerts to users based on user defined profiles.

Usage: alertengine [--test] [--loglevel=DEBUG|INFO|WARN|CRITICAL]
"""
# FIXME missing detailed usage

import getopt
import logging
import logging.handlers
import os
import os.path
import pwd
import signal
import socket
import sys
import time

import nav.config
import nav.daemon
import nav.logs
import nav.path
import nav.db

if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'nav.django.settings'

# These have to be imported after the envrionment is setup
from django.db import DatabaseError, connection
from nav.alertengine.base import check_alerts

### PATHS
configfile = os.path.join(nav.path.sysconfdir, 'alertengine.conf')
logfile = os.path.join(nav.path.localstatedir, 'log', 'alertengine.log')
pidfile = os.path.join(nav.path.localstatedir, 'run', 'alertengine.pid')

### MAIN FUNCTION

def main(args):
    # Get command line arguments
    try:
        opts, args = getopt.getopt(args, 'ht', ['help', 'test', 'loglevel='])
    except getopt.GetoptError, e:
        print >> sys.stderr, "%s\nTry `%s --help' for more information." % \
            (e, sys.argv[0])
        sys.exit(1)

    opttest = False
    optlevel = None

    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        if opt in ('-t', '--test'):
            opttest = True
        if opt == '--loglevel':
            optlevel = val

    # Set config defaults
    defaults = {
        'username': 'navcron',
        'delay': '30',
        'loglevel': 'INFO',
        'mailwarnlevel': 'ERROR',
        'mailserver': 'localhost',
        'mailaddr': nav.config.readConfig('nav.conf')['ADMIN_MAIL']
    }


    # Read config file
    config = nav.config.getconfig(configfile, defaults)

    # Set variables based on config
    username = config['main']['username']
    delay = int(config['main']['delay'])
    loglevel = eval('logging.' + (optlevel or config['main']['loglevel']))
    mailwarnlevel = eval('logging.' + config['main']['mailwarnlevel'])
    mailserver = config['main']['mailserver']
    mailaddr = config['main']['mailaddr']

    # Initialize logger
    global logger
    logger = logging.getLogger('nav.alertengine')
    logger.setLevel(1) # Let all info through to the root node
    loginitstderr(loglevel)

    # Switch user to navcron (only works if we're root)
    if not opttest:
        try:
            nav.daemon.switchuser(username)
        except nav.daemon.DaemonError, e:
            logger.error("%s Run as root or %s to enter daemon mode. " \
                + "Try `%s --help' for more information.",
                e, username, sys.argv[0])
            sys.exit(1)

    # Init daemon loggers
    if not loginitfile(loglevel, logfile):
        sys.exit(1)
    if not loginitsmtp(mailwarnlevel, mailaddr, mailserver):
        sys.exit(1)

    # Check if already running
    try:
        nav.daemon.justme(pidfile)
    except nav.daemon.DaemonError, e:
        logger.error(e)
        sys.exit(1)

    # Daemonize
    if not opttest:
        try:
            nav.daemon.daemonize(pidfile,
                                 stderr=nav.logs.get_logfile_from_logger())
        except nav.daemon.DaemonError, e:
            logger.error(e)
            sys.exit(1)

    # Stop logging explicitly to stderr
    loguninitstderr()

    # Reopen log files on SIGHUP
    signal.signal(signal.SIGHUP, signalhandler)
    signal.signal(signal.SIGTERM, signalhandler)

    # Loop forever
    logger.info('Starting alertengine loop.')
    while True:
        try:
            # Changing the isolation level is done to prevent idle transactions
            # between runs. Isolation level 0 = autocommit and level 1 = read
            # commited.
            if connection.connection and not connection.connection.closed:
                connection.connection.set_isolation_level(1)

            check_alerts(debug=opttest)

            if connection.connection and not connection.connection.closed:
                connection.connection.set_isolation_level(0)

            # nav.db connections are currently not in autocommit mode, and
            # since the current auth code uses legacy db connections we need to
            # be sure that we end all and any transactions so that we don't
            # idle.
            conns = [v.object for v in nav.db._connectionCache.values()]
            for conn in conns:
                conn.commit()

        except DatabaseError, e:
            logger.error('Database error, closing the DB connection just in case:\n%s' % e)
            logger.debug('', exc_info=True)
            if connection.queries:
                logger.debug(connection.queries[-1]['sql'])
            connection.close()

        except Exception, e:
            logger.critical('Unhandled error: %s' % e, exc_info=True)
            sys.exit(1)

        # Devel only
        if opttest:
            break
        else:
            # Sleep a bit before the next run
            logger.debug('Sleeping for %d seconds.', delay)
            time.sleep(delay)

    # Exit nicely
    sys.exit(0)


### HELPER FUNCTIONS

def signalhandler(signum, _):
    """Signal handler to close and reopen log file(s) on HUP and exit on TERM."""

    if signum == signal.SIGHUP:
        logger.info('SIGHUP received; reopening log files.')
        nav.logs.reopen_log_files()
        nav.daemon.redirect_std_fds(
            stderr=nav.logs.get_logfile_from_logger())
        logger.info('Log files reopened.')
    elif signum == signal.SIGTERM:
        logger.warn('SIGTERM received: Shutting down')
        sys.exit(0)

def loginitfile(loglevel, filename):
    """Initalize the logging handler for logfile."""

    try:
        filehandler = logging.FileHandler(filename, 'a')
        fileformat = '[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s'
        fileformatter = logging.Formatter(fileformat)
        filehandler.setFormatter(fileformatter)
        filehandler.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(filehandler)
        return True
    except IOError, error:
        print >> sys.stderr, \
         "Failed creating file loghandler. Daemon mode disabled. (%s)" \
         % error
        return False

def loginitstderr(loglevel):
    """Initalize the logging handler for stderr."""

    try:
        stderrhandler = logging.StreamHandler(sys.stderr)
        stderrformat = '%(levelname)s %(message)s'
        stderrformatter = logging.Formatter(stderrformat)
        stderrhandler.setFormatter(stderrformatter)
        stderrhandler.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(stderrhandler)
        return True
    except IOError, error:
        print >> sys.stderr, \
         "Failed creating stderr loghandler. Daemon mode disabled. (%s)" \
         % error
        return False

def loguninitstderr():
    """Remove the stderr StreamHandler from the root logger."""
    for hdlr in logging.root.handlers:
        if isinstance(hdlr, logging.StreamHandler) and hdlr.stream is sys.stderr:
            logging.root.removeHandler(hdlr)
            return True

def loginitsmtp(loglevel, mailaddr, mailserver):
    """Initalize the logging handler for SMTP."""

    try:
        # localuser will be root if alertengine was started as root, since
        # switchuser() is first called at a later time
        localuser = pwd.getpwuid(os.getuid())[0]
        hostname = socket.gethostname()
        fromaddr = localuser + '@' + hostname

        mailhandler = logging.handlers.SMTPHandler(mailserver, fromaddr,
         mailaddr, 'NAV alertengine warning from ' + hostname)
        mailformat = '[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s'
        mailformatter = logging.Formatter(mailformat)
        mailhandler.setFormatter(mailformatter)
        mailhandler.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(mailhandler)
        return True
    except Exception, error:
        print >> sys.stderr, \
         "Failed creating SMTP loghandler. Daemon mode disabled. (%s)" \
         % error
        return False

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


### BEGIN
if __name__ == '__main__':
    main(sys.argv[1:])
