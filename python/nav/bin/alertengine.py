#!/usr/bin/env python
# -*- testargs: --test -*-
#
# Copyright (C) 2007, 2008, 2011, 2013, 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
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

from nav.bootstrap import bootstrap_django

bootstrap_django(__file__)

import nav.buildconf
import nav.config
import nav.daemon
import nav.logs
import nav.buildconf
import nav.db


# These have to be imported after the envrionment is setup
from django.db import DatabaseError, connection
from nav.alertengine.base import check_alerts, clear_blacklisted_status_of_alert_senders
from nav.config import NAV_CONFIG

#
#  PATHS
#
configfile = 'alertengine.conf'
logfile = os.path.join(NAV_CONFIG['LOG_DIR'], 'alertengine.log')
pidfile = 'alertengine.pid'

_logger = logging.getLogger('nav.alertengine')

#
# MAIN FUNCTION
#


def main():
    args = parse_args()

    # Set config defaults
    defaults = {
        'username': nav.config.NAV_CONFIG['NAV_USER'],
        'delay': '30',
        'mailwarnlevel': 'ERROR',
        'mailserver': 'localhost',
        'mailaddr': nav.config.NAV_CONFIG['ADMIN_MAIL'],
        'fromaddr': nav.config.NAV_CONFIG['DEFAULT_FROM_EMAIL'],
    }

    # Read config file
    config = nav.config.getconfig(configfile, defaults)

    # Set variables based on config
    username = config['main']['username']
    delay = int(config['main']['delay'])
    mailwarnlevel = config['main']['mailwarnlevel']
    if mailwarnlevel.isdigit():
        mailwarnlevel = int(mailwarnlevel)
    else:
        mailwarnlevel = getattr(logging, mailwarnlevel)
    mailserver = config['main']['mailserver']
    mailaddr = config['main']['mailaddr']
    fromaddr = config['main']['fromaddr']

    # Switch user to $NAV_USER (navcron) (only works if we're root)
    if os.geteuid() == 0 and not args.test:
        try:
            nav.daemon.switchuser(username)
        except nav.daemon.DaemonError as err:
            print(err, file=sys.stderr)
            print(
                "Run as root or %s. Try `%s --help' for more information."
                % (username, sys.argv[0]),
                file=sys.stderr,
            )
            sys.exit(1)

    # Initialize logger
    nav.logs.init_stderr_logging()

    # Init SMTP logging of grave errors
    if not loginitsmtp(mailwarnlevel, mailaddr, fromaddr, mailserver):
        sys.exit(1)

    # Check if already running
    try:
        nav.daemon.justme(pidfile)
    except nav.daemon.DaemonError as error:
        _logger.error(error)
        sys.exit(1)

    # Daemonize
    if not args.test and not args.foreground:
        try:
            nav.daemon.daemonize(pidfile, stderr=open(logfile, "a"))
        except nav.daemon.DaemonError as error:
            _logger.error(error)
            sys.exit(1)

        # Reopen log files on SIGHUP
        signal.signal(signal.SIGHUP, signalhandler)
    else:
        nav.daemon.writepidfile(pidfile)

    # Log reception of SIGTERM/SIGINT before quitting
    signal.signal(signal.SIGTERM, signalhandler)
    signal.signal(signal.SIGINT, signalhandler)

    clear_blacklisted_status_of_alert_senders()

    # Loop forever
    _logger.info('Starting alertengine loop.')
    while True:
        try:
            check_alerts(debug=args.test)
            # nav.db connections are currently not in autocommit mode, and
            # since the current auth code uses legacy db connections we need to
            # be sure that we end all and any transactions so that we don't
            # idle.
            nav.db.commit_all_connections()

        except DatabaseError as err:
            _logger.error(
                'Database error, closing the DB connection just in case:\n%s', err
            )
            _logger.debug('', exc_info=True)
            if connection.queries:
                _logger.debug(connection.queries[-1]['sql'])
            try:
                connection.close()
            except InterfaceError:
                connection.connection = None

        except Exception as err:  # noqa: BLE001
            _logger.critical('Unhandled error: %s', err, exc_info=True)
            sys.exit(1)

        # Devel only
        if args.test:
            break
        else:
            # Sleep a bit before the next run
            _logger.debug('Sleeping for %d seconds.', delay)
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
        "from the event engine and sends notifications to users based "
        "on user defined profiles.",
    )
    parser.add_argument(
        "-t",
        "--test",
        action="store_true",
        help="process the alert queue once and exit",
    )
    parser.add_argument(
        "-f", "--foreground", action="store_true", help="run in the foreground"
    )

    return parser.parse_args()


def signalhandler(signum, _):
    """Signal handler to close and reopen log file(s) on HUP and exit on TERM"""

    if signum == signal.SIGHUP:
        _logger.info('SIGHUP received; reopening log files.')
        nav.logs.reopen_log_files()
        nav.daemon.redirect_std_fds(stderr=open(logfile, "a"))
        nav.logs.reset_log_levels()
        nav.logs.set_log_config()
        _logger.info('Log files reopened.')
    elif signum == signal.SIGTERM:
        _logger.warning('SIGTERM received: Shutting down')
        sys.exit(0)
    elif signum == signal.SIGINT:
        _logger.warning('SIGINT received: Shutting down')
        sys.exit(0)


def loginitsmtp(loglevel, mailaddr, fromaddr, mailserver):
    """Initalize the logging handler for SMTP."""

    try:
        hostname = socket.gethostname()
        mailhandler = logging.handlers.SMTPHandler(
            mailserver, fromaddr, mailaddr, 'NAV alertengine warning from ' + hostname
        )
        mailformat = (
            '[%(asctime)s] [%(levelname)s] [pid=%(process)d %(name)s] %(message)s'
        )
        mailformatter = logging.Formatter(mailformat)
        mailhandler.setFormatter(mailformatter)
        mailhandler.setLevel(loglevel)
        _logger = logging.getLogger()
        _logger.addHandler(mailhandler)
        return True
    except Exception as error:  # noqa: BLE001
        print(
            "Failed creating SMTP loghandler. Daemon mode disabled. (%s)" % error,
            file=sys.stderr,
        )
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
        _logger.info("Setting delay to %d seconds.", sec)
        return True
    else:
        _logger.warning("Given delay not a digit. Using default.")
        return False


if __name__ == '__main__':
    main()
