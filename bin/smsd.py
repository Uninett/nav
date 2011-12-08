#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006-2008 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""The NAV SMS daemon (smsd)

smsd dispatches SMS messages from the database to users' phones with the help
of plugins using Gammu and a cell on the COM port, or free SMS services on the
web.

Usage: smsd [-h] [-c] [-d sec] [-f factor] [-m maxdelay] [-l limit] [-a action] [-tT phone no.] [-u user ID]

  -h, --help            Show this help text
  -c, --cancel          Cancel (mark as ignored) all unsent messages
  -d, --delay           Set delay (in seconds) between queue checks
  -f, --factor          Set the factor delay will be multiplied with
  -m, --maxdelay        Maximum delay (in seconds)
  -l, --limit           Set the limit of retries
  -a, --action          The action to perform when reaching limit (0 or 1)
                          0: Messages in queue are marked as ignored and error
                             details are logged and mailed to admin. Deamon
                             resumes running and checking the message queue.
                          1: Error details are logged and mailed to admin. The
                             deamon shuts down.
  -u, --uid             User/account ID
  -t, --test            Send a test message to <phone no.>
  -T, --TEST            Put a test message to <phone no.> into the SMS queue

"""

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
import nav.smsd.navdbqueue
from nav.smsd.dispatcher import DispatcherError, PermanentDispatcherError
from nav.config import getconfig
# Dispatchers are imported later according to config


### PATHS

configfile = os.path.join(nav.path.sysconfdir, 'smsd.conf')
logfile = os.path.join(nav.path.localstatedir, 'log', 'smsd.log')
pidfile = os.path.join(nav.path.localstatedir, 'run', 'smsd.pid')

### MAIN FUNCTION

def main(args):
    # Get command line arguments
    optcancel = False
    optdelay = False
    optfactor = False
    optmaxdelay = False
    optlimit = False
    optaction = False
    opttest = False
    optuid = False
    try:
        opts, args = getopt.getopt(args, 'hcd:f:m:l:a:t:T:u:',
         ['help', 'cancel', 'delay=', 'test=', 'TEST=', 'uid='])
    except getopt.GetoptError, error:
        print >> sys.stderr, "%s\nTry `%s --help' for more information." % (
            error, sys.argv[0])
        sys.exit(1)
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(0)
        if opt in ('-c', '--cancel'):
            optcancel = True
        if opt in ('-d', '--delay'):
            optdelay = int(val)
        if opt in ('-f', '--factor'):
            optfactor = int(val)
        if opt in ('-m', '--maxdelay'):
            optmaxdelay = int(val)
        if opt in ('-l', '--limit'):
            optlimit = int(val)
        if opt in ('-a', '--action'):
            optaction = int(val)
        if opt in ('-t', '--test', '-T', '--TEST'):
            opttest = { 'opt': opt, 'val': val}
        if opt in ('-u', '--uid'):
            optuid = int(val)


    # Set config defaults
    global defaults
    defaults = {
        'username': 'navcron',
        'delay': '30',
        'delayfactor': '1.5',
        'maxdelay': '3600',
        'retrylimit': '5',
        'retrylimitaction': 'ignore',
        'exit_on_permanent_error': 'yes',
        'autocancel': '0',
        'loglevel': 'INFO',
        'mailwarnlevel': 'ERROR',
        'mailserver': 'localhost',
        'mailaddr': nav.config.readConfig('nav.conf')['ADMIN_MAIL']
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
        'retrylimitaction': retrylimitaction
    }

    exit_on_permanent_error = (
        config['main']['exit_on_permanent_error'].lower() in ('yes', 'true'))

    username = config['main']['username']
    autocancel = config['main']['autocancel']
    loglevel = eval('logging.' + config['main']['loglevel'])
    mailwarnlevel = eval('logging.' + config['main']['mailwarnlevel'])
    mailserver = config['main']['mailserver']
    mailaddr = config['main']['mailaddr']

    # Initialize logger
    global logger
    nav.logs.set_log_levels()
    logger = logging.getLogger('nav.smsd')
    loginitstderr(loglevel)
    if not loginitfile(loglevel, logfile):
        sys.exit('Failed to init file logging.')
    if not loginitsmtp(mailwarnlevel, mailaddr, mailserver):
        sys.exit('Failed to init SMTP logging.')


    # First log message
    logger.info('Starting smsd.')


    # Set custom loop delay
    if optdelay:
        setdelay(optdelay)

    # Ignore unsent messages
    if optcancel:
        queue = nav.smsd.navdbqueue.NAVDBQueue()
        ignCount = queue.cancel()
        logger.info("All %d unsent messages ignored.", ignCount)
        sys.exit(0)

    if optfactor:
        retryvars['delayfactor'] = optfactor
    if optmaxdelay:
        retryvars['maxdelay'] = optmaxdelay
    if optlimit:
        retryvars['retrylimit'] = optlimit
    if optaction:
        retryvars['retrylimitaction'] = optaction

    # Let the dispatcherhandler take care of our dispatchers
    try:
        dh = nav.smsd.dispatcher.DispatcherHandler(config)
    except PermanentDispatcherError, error:
        logger.critical("Dispatcher configuration failed. Exiting. (%s)", error)
        sys.exit(1)

    # Send test message (in other words: test the dispatcher)
    if opttest:
        msg = [(0, "This is a test message from NAV smsd.", 0)]

        if opttest['opt'] in ('-t', '--test'):
            try:
                (sms, sent, ignored, smsid) = dh.sendsms(opttest['val'], msg)
            except DispatcherError, error:
                logger.critical("Sending failed. Exiting. (%s)", error)
                sys.exit(1)

            logger.info("SMS sent. Dispatcher returned reference %d.", smsid)

        elif opttest['opt'] in ('-T', '--TEST') and optuid:
            queue = nav.smsd.navdbqueue.NAVDBQueue()
            rowsinserted = queue.inserttestmsgs(optuid, opttest['val'],
                'This is a test message from NAV smsd.')
            if rowsinserted:
                logger.info("SMS put in queue. %d row(s) inserted.", rowsinserted)
            else:
                logger.info("SMS not put in queue.")

        sys.exit(0)

    # Switch user to navcron (only works if we're root)
    try:
        nav.daemon.switchuser(username)
    except nav.daemon.DaemonError, error:
        logger.error("%s Run as root or %s to enter daemon mode. "
            + "Try `%s --help' for more information.",
            error, username, sys.argv[0])
        sys.exit(1)

    # Check if already running
    try:
        nav.daemon.justme(pidfile)
    except nav.daemon.DaemonError, error:
        logger.error(error)
        sys.exit(1)

    # Daemonize
    try:
        nav.daemon.daemonize(pidfile,
                             stderr=nav.logs.get_logfile_from_logger())
    except nav.daemon.DaemonError, error:
        logger.error(error)
        sys.exit(1)

    # Daemonized; stop logging explicitly to stderr and reopen log files
    loguninitstderr()
    nav.logs.reopen_log_files()
    logger.debug('Daemonization complete; reopened log files.')

    # Reopen log files on SIGHUP
    logger.debug('Adding signal handler for reopening log files on SIGHUP.')
    signal.signal(signal.SIGHUP, signalhandler)
    # Exit on SIGTERM
    signal.signal(signal.SIGTERM, signalhandler)

    # Initialize queue
    # NOTE: If we're initalizing a queue with a DB connection before
    # daemonizing we've experienced that the daemon dies silently upon trying
    # to use the DB connection after becoming a daemon
    queue = nav.smsd.navdbqueue.NAVDBQueue()

    # Automatically cancel unsent messages older than a given interval
    if autocancel != '0':
        ignCount = queue.cancel(autocancel)
        logger.info("%d unsent messages older than '%s' autocanceled.",
            ignCount, autocancel)


    # Loop forever
    while True:
        logger.debug("Starting loop.")

        # Queue: Get users with unsent messages
        users = queue.getusers('N')

        logger.info("Found %d user(s) with unsent messages.", len(users))

        # Loop over cell numbers
        for user in users:
            # Queue: Get unsent messages for a user ordered by severity desc
            msgs = queue.getusermsgs(user, 'N')
            logger.info("Found %d unsent message(s) for %s.", len(msgs), user)

            # Dispatcher: Format and send SMS
            try:
                (sms, sent, ignored, smsid) = dh.sendsms(user, msgs)
            except DispatcherError, error:
                if exit_on_permanent_error:
                    if isinstance(error, PermanentDispatcherError):
                        logger.critical(
                            "Sending failed permanently. Exiting. (%s)", error)
                        sys.exit(1)

                try:
                    # Dispatching failed. Backing off.
                    backoff(delay, error, retryvars)

                    break # End this run
                except:
                    logger.exception("")
                    raise
            except Exception, error:
                logger.exception("Unknown exception: %s", error)


            logger.info("SMS sent to %s.", user)

            if failed:
                resetdelay()
                failed = 0
                logger.debug("Resetting delay and number of failed runs.")

            for msgid in sent:
                queue.setsentstatus(msgid, 'Y', smsid)
            for msgid in ignored:
                queue.setsentstatus(msgid, 'I', smsid)
            logger.info("%d messages was sent and %d ignored.",
                len(sent), len(ignored))

        # Sleep a bit before the next run
        logger.debug("Sleeping for %d seconds.", delay)
        time.sleep(delay)

        # Devel only
        #break

    # Exit nicely
    sys.exit(0)


### HELPER FUNCTIONS

def setdelay(seconds):
    """Set delay (in seconds) between queue checks."""

    global delay, logger

    delay = seconds
    logger.info("Setting delay to %d seconds.", delay)


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

    # Function is invoked with the assumption that there are unsent messages in queue.
    global failed

    maxdelay, delayfactor, retrylimit, retrylimitaction = retryvars['maxdelay'], \
        retryvars['delayfactor'], retryvars['retrylimit'], \
        retryvars['retrylimitaction']

    failed += 1
    logger.debug("Dispatcher failed %d time(s).", failed)
    increasedelay(seconds, delayfactor, maxdelay)

    queue = nav.smsd.navdbqueue.NAVDBQueue()
    msgs = queue.getmsgs('N')

    # If limit is set and reached, perform an action
    if retrylimit != 0 and failed >= retrylimit:
        backoffaction(error, retrylimitaction)

    # If limit is disabled, report error and continue
    elif retrylimit == 0 and delay >= maxdelay:
        if len(msgs):
            logger.critical("Dispatching SMS fails. %d unsent message(s),"
                " the oldest from %s. (%s)", len(msgs), msgs[0]['time'], error)
        else:
            logger.critical("Dispatching SMS fails. (%s)", error)


def backoffaction(error, retrylimitaction):
    """Perform an action if the retry limit has been reached."""

    global failed
    queue = nav.smsd.navdbqueue.NAVDBQueue()
    msgs = queue.getmsgs('N')

    if retrylimitaction == "ignore":
        # Queued messages are marked as ignored, logs a critical error with
        # message details, then resumes run.
        numbmsg = queue.cancel()
        error_message = (u"Dispatch retry limit has been reached."
            " Dispatching SMS has failed %s times. Ignoring %s message(s)." %
            (failed, numbmsg))

        for index, msg in enumerate(msgs):
            error_message += u"\n%s: \"%s\" --> %s" % (
                index+1,
                msg['msg'].decode('utf-8'), msg['name'].decode('utf-8'))

        error_message += u"\nError message: %s" % error
        logger.critical(error_message.encode('utf-8'))
        failed = 0
        resetdelay()


    elif retrylimitaction == "shutdown":
        # Logs the number of unsent messages and time of the oldest in queue
        # before shutting down daemon.
        logger.critical("Dispatch retry limit has been reached."
            " Dispatching SMS has failed %d times. %d unsent message(s), the oldest from %s."
            " \nError message: %s \nShutting down daemon.\n",
            failed, len(msgs), msgs[0]["time"], error)
        sys.exit(0)

    else:
        logger.warning("No retry limit action is set or the configured option is not valid.")


def signalhandler(signum, _):
    """
    Signal handler to close and reopen log file(s) on HUP
    and exit on KILL.
    """

    if signum == signal.SIGHUP:
        global logger
        logger.info("SIGHUP received; reopening log files.")
        nav.logs.reopen_log_files()
        nav.daemon.redirect_std_fds(
            stderr=nav.logs.get_logfile_from_logger())
        logger.info("Log files reopened.")
    elif signum == signal.SIGTERM:
        logger.warn('SIGTERM received: Shutting down.')
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
        stderrformat = '[%(levelname)s] [pid=%(process)d %(name)s] %(message)s'
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
        # localuser will be root if smsd was started as root, since
        # switchuser() is first called at a later time
        localuser = pwd.getpwuid(os.getuid())[0]
        hostname = socket.gethostname()
        fromaddr = localuser + '@' + hostname

        mailhandler = logging.handlers.SMTPHandler(mailserver, fromaddr,
            mailaddr, 'NAV smsd warning from ' + hostname)
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

### BEGIN
if __name__ == '__main__':
    main(sys.argv[1:])
