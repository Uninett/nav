#!/usr/bin/env python
# -*- testargs: --test -*-
#
# Copyright (C) 2007, 2008, 2011, 2013, 2017 Uninett AS
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
"""

from __future__ import print_function

# FIXME missing detailed usage

import argparse
import logging
import logging.handlers
import os
import os.path
import signal
import socket
import sys
import time
from psycopg2 import InterfaceError

import nav.buildconf
import nav.config
import nav.daemon
import nav.logs
import nav.buildconf
import nav.db


# These have to be imported after the envrionment is setup
from django.db import DatabaseError, connection
from nav.alertengine.base import check_alerts

#
#  PATHS
#
configfile = os.path.join(nav.buildconf.sysconfdir, 'alertengine.conf')
logfile = os.path.join(nav.buildconf.localstatedir, 'log', 'alertengine.log')
pidfile = os.path.join(nav.buildconf.localstatedir, 'run', 'alertengine.pid')

logger = None

#
# MAIN FUNCTION
#


def main():
    args = parse_args()

    # Set config defaults
    defaults = {
        'username': nav.buildconf.nav_user,
        'delay': '30',
        'loglevel': 'INFO',
        'mailwarnlevel': 'ERROR',
        'mailserver': 'localhost',
        'mailaddr': nav.config.read_flat_config('nav.conf')['ADMIN_MAIL'],
        'fromaddr': nav.config.read_flat_config('nav.conf')[
            'DEFAULT_FROM_EMAIL'],
    }

    # Read config file
    config = nav.config.getconfig(configfile, defaults)

    # Set variables based on config
    username = config['main']['username']
    delay = int(config['main']['delay'])
    loglevel = eval('logging.' + (args.loglevel or config['main']['loglevel']))
    mailwarnlevel = eval('logging.' + config['main']['mailwarnlevel'])
    mailserver = config['main']['mailserver']
    mailaddr = config['main']['mailaddr']
    fromaddr = config['main']['fromaddr']

    # Initialize logger
    global logger
    logger = logging.getLogger('nav.alertengine')
    logger.setLevel(1)  # Let all info through to the root node
    loginitstderr(loglevel)

    # Switch user to $NAV_USER (navcron) (only works if we're root)
    if os.geteuid() == 0 and not args.test:
        try:
            nav.daemon.switchuser(username)
        except nav.daemon.DaemonError as err:
            logger.error("%s Run as root or %s to enter daemon mode. "
                         "Try `%s --help' for more information.",
                         err, username, sys.argv[0])
            sys.exit(1)

    # Init daemon loggers
    if not loginitfile(loglevel, logfile):
        sys.exit(1)
    if not loginitsmtp(mailwarnlevel, mailaddr, fromaddr, mailserver):
        sys.exit(1)

    # Check if already running
    try:
        nav.daemon.justme(pidfile)
    except nav.daemon.DaemonError as error:
        logger.error(error)
        sys.exit(1)

    # Daemonize
    if not args.test and not args.foreground:
        try:
            nav.daemon.daemonize(pidfile,
                                 stderr=nav.logs.get_logfile_from_logger())
        except nav.daemon.DaemonError as error:
            logger.error(error)
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
            check_alerts(debug=args.test)
            # nav.db connections are currently not in autocommit mode, and
            # since the current auth code uses legacy db connections we need to
            # be sure that we end all and any transactions so that we don't
            # idle.
            nav.db.commit_all_connections()

        except DatabaseError as err:
            logger.error('Database error, closing the DB connection just in '
                         'case:\n%s', err)
            logger.debug('', exc_info=True)
            if connection.queries:
                logger.debug(connection.queries[-1]['sql'])
            try:
                connection.close()
            except InterfaceError:
                connection.connection = None

        except Exception as err:
            logger.critical('Unhandled error: %s', err, exc_info=True)
            sys.exit(1)

        # Devel only
        if args.test:
            break
        else:
            # Sleep a bit before the next run
            logger.debug('Sleeping for %d seconds.', delay)
            time.sleep(delay)

    # Exit nicely
    sys.exit(0)


#
# HELPER FUNCTIONS
#


def parse_args():
    """Parses command line arguments using argparse"""
    parser = argparse.ArgumentParser(
        description="The NAV Alert Engine daemon",
        epilog="This background process polls the alert queue for new alerts "
               "from the event engine and sends put alerts to users based on "
               "user defined profiles.",
    )
    parser.add_argument("-t", "--test", action="store_true",
                        help="process the alert queue once and exit")
    parser.add_argument("-f", "--foreground", action="store_true",
                        help="run in the foreground")

    levels = getattr(logging, '_levelNames', {})
    levels = [name for lvl, name in sorted(levels.items()) if type(lvl) is int]
    parser.add_argument("--loglevel", metavar="LEVEL", choices=levels,
                        help="set the daemon log level")

    return parser.parse_args()


def signalhandler(signum, _):
    """Signal handler to close and reopen log file(s) on HUP and exit on TERM"""

    if signum == signal.SIGHUP:
        logger.info('SIGHUP received; reopening log files.')
        nav.logs.reopen_log_files()
        nav.daemon.redirect_std_fds(
            stderr=nav.logs.get_logfile_from_logger())
        logger.info('Log files reopened.')
    elif signum == signal.SIGTERM:
        logger.warning('SIGTERM received: Shutting down')
        sys.exit(0)


def loginitfile(loglevel, filename):
    """Initalize the logging handler for logfile."""

    try:
        filehandler = logging.FileHandler(filename, 'a')
        fileformat = (
            '[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] '
            '%(message)s')
        fileformatter = logging.Formatter(fileformat)
        filehandler.setFormatter(fileformatter)
        filehandler.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(filehandler)
        return True
    except IOError as error:
        print("Failed creating file loghandler. Daemon mode disabled. (%s)"
              % error, file=sys.stderr)
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
    except IOError as error:
        print("Failed creating stderr loghandler. Daemon mode disabled. (%s)"
              % error, file=sys.stderr)
        return False


def loguninitstderr():
    """Remove the stderr StreamHandler from the root logger."""
    for hdlr in logging.root.handlers:
        if isinstance(hdlr, logging.StreamHandler) and hdlr.stream is sys.stderr:
            logging.root.removeHandler(hdlr)
            return True


def loginitsmtp(loglevel, mailaddr, fromaddr, mailserver):
    """Initalize the logging handler for SMTP."""

    try:
        hostname = socket.gethostname()
        mailhandler = logging.handlers.SMTPHandler(
            mailserver, fromaddr, mailaddr,
            'NAV alertengine warning from ' + hostname)
        mailformat = (
            '[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] '
            '%(message)s')
        mailformatter = logging.Formatter(mailformat)
        mailhandler.setFormatter(mailformatter)
        mailhandler.setLevel(loglevel)
        logger = logging.getLogger()
        logger.addHandler(mailhandler)
        return True
    except Exception as error:
        print("Failed creating SMTP loghandler. Daemon mode disabled. (%s)"
              % error, file=sys.stderr)
        return False


def usage():
    """Print a usage screen to stderr."""
    print(__doc__, file=sys.stderr)


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


if __name__ == '__main__':
    main()
