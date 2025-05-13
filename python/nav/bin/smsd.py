#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- testargs: -c -*-
#
# Copyright (C) 2006-2008, 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""The NAV SMS daemon"""

import argparse
import logging
import logging.handlers
import os
import os.path
import signal
import socket
import sys
import time

from django.utils.encoding import smart_str

import nav.config
import nav.daemon
import nav.logs
import nav.smsd.navdbqueue
from nav.smsd.dispatcher import DispatcherError, PermanentDispatcherError
from nav.config import getconfig, NAV_CONFIG
from nav.bootstrap import bootstrap_django

# Dispatchers are imported later according to config


#
#  PATHS
#
configfile = 'smsd.conf'
logfile = os.path.join(NAV_CONFIG['LOG_DIR'], 'smsd.log')
pidfile = os.path.join(NAV_CONFIG['PID_DIR'], 'smsd.pid')

#
# Logging
#
_logger = logging.getLogger('nav.smsd')

#
# Globals
#
config = delay = failed = defaults = None

#
#  MAIN FUNCTION
#


def main():
    bootstrap_django()
    args = parse_args()

    # Set config defaults
    global defaults
    defaults = {
        'username': NAV_CONFIG['NAV_USER'],
        'delay': '30',
        'delayfactor': '1.5',
        'maxdelay': '3600',
        'retrylimit': '5',
        'retrylimitaction': 'ignore',
        'exit_on_permanent_error': 'yes',
        'autocancel': '0',
        'mailwarnlevel': 'ERROR',
        'mailserver': 'localhost',
        'mailaddr': NAV_CONFIG['ADMIN_MAIL'],
        'fromaddr': NAV_CONFIG['DEFAULT_FROM_EMAIL'],
    }

    # Read config file
    global config
    config = getconfig(configfile, defaults)

    # Set variables
    global delay, failed
    failed = 0
    delay = int(config['main']['delay'])
    maxdelay = int(config['main']['maxdelay'])
    delayfactor = float(config['main']['delayfactor'])
    retrylimit = int(config['main']['retrylimit'])
    retrylimitaction = config['main']['retrylimitaction'].strip()
    retryvars = {
        'maxdelay': maxdelay,
        'delayfactor': delayfactor,
        'retrylimit': retrylimit,
        'retrylimitaction': retrylimitaction,
    }

    username = config['main']['username']
    autocancel = config['main']['autocancel']
    mailwarnlevel = logging.getLevelName(config['main']['mailwarnlevel'])
    mailserver = config['main']['mailserver']
    mailaddr = config['main']['mailaddr']
    fromaddr = config['main']['fromaddr']

    # Drop privileges if running as root
    if os.geteuid() == 0:
        try:
            nav.daemon.switchuser(username)
        except nav.daemon.DaemonError as error:
            print(error, file=sys.stderr)
            sys.exit(
                "Run as root or %s. Try `%s --help' for more information."
                % (username, sys.argv[0])
            )

    # Initialize logging
    nav.logs.init_stderr_logging()
    if not loginitsmtp(mailwarnlevel, mailaddr, fromaddr, mailserver):
        sys.exit('Failed to init SMTP logging.')

    # First log message
    _logger.info('Starting smsd.')

    # Set custom loop delay
    if args.delay:
        setdelay(args.delay)

    # Ignore unsent messages
    if args.cancel:
        queue = nav.smsd.navdbqueue.NAVDBQueue()
        ignored_count = queue.cancel()
        _logger.info("All %d unsent messages ignored.", ignored_count)
        sys.exit(0)

    if args.delayfactor:
        retryvars['delayfactor'] = args.delayfactor
    if args.maxdelay:
        retryvars['maxdelay'] = args.maxdelay
    if args.limit:
        retryvars['retrylimit'] = args.limit
    if args.action:
        retryvars['retrylimitaction'] = args.action

    # Let the dispatcherhandler take care of our dispatchers
    try:
        dh = nav.smsd.dispatcher.DispatcherHandler(config)
    except PermanentDispatcherError as error:
        _logger.critical("Dispatcher configuration failed. Exiting. (%s)", error)
        sys.exit(1)

    # Send test message (in other words: test the dispatcher)
    if args.test or args.TEST:
        text = args.message or "This is a test message from NAV smsd."

        if args.test:
            msg = [(0, text, 0)]
            try:
                (sms, sent, ignored, smsid) = dh.sendsms(args.test, msg)
            except DispatcherError as error:
                _logger.critical("Sending failed. Exiting. (%s)", error)
                sys.exit(1)

            _logger.info("SMS sent. Dispatcher returned reference %d.", smsid)

        elif args.TEST and args.uid:
            queue = nav.smsd.navdbqueue.NAVDBQueue()
            rowsinserted = queue.inserttestmsgs(args.uid, args.TEST, text)
            if rowsinserted:
                _logger.info("SMS put in queue. %d row(s) inserted.", rowsinserted)
            else:
                _logger.info("SMS not put in queue.")

        sys.exit(0)

    # Check if already running
    try:
        nav.daemon.justme(pidfile)
    except nav.daemon.DaemonError as error:
        _logger.error(error)
        sys.exit(1)

    # Daemonize
    if not args.foreground:
        try:
            nav.daemon.daemonize(pidfile, stderr=open(logfile, "a"))
        except nav.daemon.DaemonError as error:
            _logger.error(error)
            sys.exit(1)

        _logger.info('smsd now running in daemon mode')
        # Reopen log files on SIGHUP
        _logger.debug('Adding signal handler for reopening log files on SIGHUP.')
        signal.signal(signal.SIGHUP, signalhandler)
    else:
        nav.daemon.writepidfile(pidfile)

    # Exit on SIGTERM/SIGINT
    signal.signal(signal.SIGTERM, signalhandler)
    signal.signal(signal.SIGINT, signalhandler)

    # Initialize queue
    # NOTE: If we're initalizing a queue with a DB connection before
    # daemonizing we've experienced that the daemon dies silently upon trying
    # to use the DB connection after becoming a daemon
    queue = nav.smsd.navdbqueue.NAVDBQueue()

    # Automatically cancel unsent messages older than a given interval
    if autocancel != '0':
        ignored_count = queue.cancel(autocancel)
        _logger.info(
            "%d unsent messages older than '%s' autocanceled.",
            ignored_count,
            autocancel,
        )

    # Loop forever
    while True:
        _logger.debug("Starting loop.")

        # Queue: Get users with unsent messages
        users = queue.getusers('N')

        _logger.info("Found %d user(s) with unsent messages.", len(users))

        # Loop over cell numbers
        for user in users:
            # Queue: Get unsent messages for a user ordered by severity desc
            msgs = queue.getusermsgs(user, 'N')
            _logger.info("Found %d unsent message(s) for %s.", len(msgs), user)

            # Dispatcher: Format and send SMS
            try:
                (sms, sent, ignored, smsid) = dh.sendsms(user, msgs)
            except PermanentDispatcherError as error:
                _logger.critical("Sending failed permanently. Exiting. (%s)", error)
                sys.exit(1)
            except DispatcherError as error:
                try:
                    # Dispatching failed. Backing off.
                    backoff(delay, error, retryvars)

                    break  # End this run
                except:
                    _logger.exception("")
                    raise
            except Exception as error:  # noqa: BLE001
                _logger.exception("Unknown exception: %s", error)

            _logger.info("SMS sent to %s.", user)

            if failed:
                resetdelay()
                failed = 0
                _logger.debug("Resetting delay and number of failed runs.")

            for msgid in sent:
                queue.setsentstatus(msgid, 'Y', smsid)
            for msgid in ignored:
                queue.setsentstatus(msgid, 'I', smsid)
            _logger.info(
                "%d messages were sent and %d ignored.", len(sent), len(ignored)
            )

        # Sleep a bit before the next run
        _logger.debug("Sleeping for %d seconds.", delay)
        time.sleep(delay)

        # Devel only
        # break


#
# HELPER FUNCTIONS
#


def parse_args():
    parser = argparse.ArgumentParser(
        description="The NAV SMS daemon",
        epilog="smsd dispatches SMS messages from the database to users' "
        "phones with the help of plugins, such as one using Gammu and "
        "a locally connected GSM unit, or possibly web based SMS "
        "services.",
    )
    arg = parser.add_argument
    arg(
        "-c",
        "--cancel",
        action="store_true",
        help="cancel (mark as ignored) all unsent messages",
    )
    arg("-d", "--delay", type=int, help="set delay (in seconds) between queue checks")
    arg(
        "-D",
        "--delayfactor",
        type=int,
        help="set the factor DELAY will be multiplied with for each attempt",
    )
    arg("-m", "--maxdelay", type=int, help="maximum delay (in seconds)")
    arg("-l", "--limit", type=int, help="set the limit of retries")
    arg(
        "-a",
        "--action",
        type=int,
        choices=[0, 1],
        help="the action to perform when reaching limit (0 or 1). 0 means "
        "messages in queue are marked as ignored and error details are "
        "logged and mailed to admin, while daemon resumes running and "
        "checking the message queue. 1 means error details are logged and "
        "mailed to admin, while the daemon shuts down.",
    )
    arg("-t", "--test", metavar="PHONENO", help="send a test message to PHONENO")
    arg(
        "-T",
        "--TEST",
        metavar="PHONENO",
        help="puts a test message to PHONENO into the SMS queue. use the --uid "
        "option to specify which NAV user account id to associate with "
        "the queued message",
    )
    arg(
        "--message",
        metavar="MESSAGE",
        help="Used in combination with -t or -T to specify the message content",
    )
    arg("-u", "--uid", type=int, help="NAV user/account id to queue message to")
    arg("-f", "--foreground", action="store_true", help="run process in the foreground")

    args = parser.parse_args()
    if args.test and args.TEST:
        parser.error("-t and -T are mutually exclusive, please pick one")
    if args.TEST and args.uid is None:
        parser.error("Please provide an account id using the --uid option")
    if args.message and not (args.test or args.TEST):
        parser.error("--message can only be used in combination with either -t or -T")
    return args


def setdelay(seconds):
    """Set delay (in seconds) between queue checks."""

    global delay, _logger

    delay = seconds
    _logger.info("Setting delay to %d seconds.", delay)


def resetdelay():
    global config, defaults
    try:
        setdelay(int(config['main']['delay']))
    except:
        setdelay(int(defaults['delay']))


def increasedelay(seconds, delayfactor, maxdelay):
    if seconds * delayfactor < maxdelay:
        setdelay(seconds * delayfactor)
    elif seconds == maxdelay:
        pass
    elif seconds * delayfactor >= maxdelay:
        setdelay(maxdelay)


def backoff(seconds, error, retryvars):
    """Delay next loop if dispatching SMS fails."""

    # Function is invoked with the assumption that there are unsent messages
    # in queue.
    global failed

    maxdelay, delayfactor, retrylimit, retrylimitaction = (
        retryvars['maxdelay'],
        retryvars['delayfactor'],
        retryvars['retrylimit'],
        retryvars['retrylimitaction'],
    )

    failed += 1
    _logger.debug("Dispatcher failed %d time(s).", failed)
    increasedelay(seconds, delayfactor, maxdelay)

    queue = nav.smsd.navdbqueue.NAVDBQueue()
    msgs = queue.getmsgs('N')

    # If limit is set and reached, perform an action
    if retrylimit != 0 and failed >= retrylimit:
        backoffaction(error, retrylimitaction)

    # If limit is disabled, report error and continue
    elif retrylimit == 0 and delay >= maxdelay:
        if len(msgs):
            _logger.critical(
                "Dispatching SMS fails. %d unsent message(s), the oldest from %s. (%s)",
                len(msgs),
                msgs[0]['time'],
                error,
            )
        else:
            _logger.critical("Dispatching SMS fails. (%s)", error)


def backoffaction(error, retrylimitaction):
    """Perform an action if the retry limit has been reached."""

    global failed
    queue = nav.smsd.navdbqueue.NAVDBQueue()
    msgs = queue.getmsgs('N')

    if retrylimitaction == "ignore":
        # Queued messages are marked as ignored, logs a critical error with
        # message details, then resumes run.
        numbmsg = queue.cancel()
        error_message = (
            "Dispatch retry limit has been reached. Dispatching SMS has failed %s "
            "times. Ignoring %s message(s)."
        ) % (failed, numbmsg)

        for index, msg in enumerate(msgs):
            error_message += '\n%s: "%s" --> %s' % (
                index + 1,
                smart_str(msg['msg']),
                smart_str(msg['name']),
            )

        error_message += "\nError message: %s" % error
        _logger.critical(error_message)
        failed = 0
        resetdelay()

    elif retrylimitaction == "shutdown":
        # Logs the number of unsent messages and time of the oldest in queue
        # before shutting down daemon.
        _logger.critical(
            "Dispatch retry limit has been reached. Dispatching SMS has failed %d "
            "times. %d unsent message(s), the oldest from %s. "
            "\nError message: %s "
            "\nShutting down daemon.\n",
            failed,
            len(msgs),
            msgs[0]["time"],
            error,
        )
        sys.exit(0)

    else:
        _logger.warning(
            "No retry limit action is set or the configured option is not valid."
        )


def signalhandler(signum, _):
    """
    Signal handler to close and reopen log file(s) on HUP
    and exit on KILL.
    """

    if signum == signal.SIGHUP:
        _logger.info("SIGHUP received; reopening log files.")
        nav.logs.reopen_log_files()
        nav.daemon.redirect_std_fds(stderr=open(logfile, "a"))
        nav.logs.reset_log_levels()
        nav.logs.set_log_config()
        _logger.info('Log files reopened.')
    elif signum == signal.SIGTERM:
        _logger.warning('SIGTERM received: Shutting down.')
        sys.exit(0)
    elif signum == signal.SIGINT:
        _logger.warning('SIGINT received: Shutting down.')
        sys.exit(0)


def loginitsmtp(loglevel, mailaddr, fromaddr, mailserver):
    """Initalize the logging handler for SMTP."""

    try:
        hostname = socket.gethostname()
        mailhandler = logging.handlers.SMTPHandler(
            mailserver, fromaddr, mailaddr, 'NAV smsd warning from ' + hostname
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


if __name__ == '__main__':
    main()
