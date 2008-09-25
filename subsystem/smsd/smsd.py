#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2008 UNINETT AS
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
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
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

__copyright__ = "Copyright 2006-2008 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"

import ConfigParser
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
    opttest = False
    try:
        opts, args = getopt.getopt(args, 'hcd:t:',
         ['help', 'cancel', 'delay=', 'test='])
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
            optdelay = val
        if opt in ('-t', '--test'):
            opttest = val

    # Set config defaults
    defaults = {
        'username': 'navcron',
        'delay': '30',
        'autocancel': '0',
        'loglevel': 'INFO',
        'mailwarnlevel': 'ERROR',
        'mailserver': 'localhost',
        'mailaddr': nav.config.readConfig('nav.conf')['ADMIN_MAIL']
    }

    # Read config file
    config = getconfig(defaults)

    # Set variables
    username = config['main']['username']
    delay = int(config['main']['delay'])
    autocancel = config['main']['autocancel']
    loglevel = eval('logging.' + config['main']['loglevel'])
    mailwarnlevel = eval('logging.' + config['main']['mailwarnlevel'])
    mailserver = config['main']['mailserver']
    mailaddr = config['main']['mailaddr']

    # Initialize logger
    global logger
    nav.logs.setLogLevels()
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

    # Let the dispatcherhandler take care of our dispatchers
    try:
        dh = nav.smsd.dispatcher.DispatcherHandler(config)
    except PermanentDispatcherError, error:
        logger.critical("Dispatcher configuration failed. Exiting. (%s)", error)
        sys.exit(1)

    # Send test message (in other words: test the dispatcher)
    if opttest:
        msg = [(0, "This is a test message from NAV smsd.", 0)]

        try:
            (sms, sent, ignored, smsid) = dh.sendsms(opttest, msg)
        except DispatcherError, error:
            logger.critical("Sending failed. Exiting. (%s)", error)
            sys.exit(1)

        logger.info("SMS sent. Dispatcher returned reference %d.", smsid)
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
        nav.daemon.daemonize(pidfile)
    except nav.daemon.DaemonError, error:
        logger.error(error)
        sys.exit(1)

    # Daemonized; reopen log files
    nav.logs.reopen_log_files()
    logger.debug('Daemonization complete; reopened log files.')

    # Reopen log files on SIGHUP
    logger.debug('Adding signal handler for reopening log files on SIGHUP.')
    signal.signal(signal.SIGHUP, signalhandler)

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
            except PermanentDispatcherError, error:
                logger.critical("Sending failed permanently. Exiting. (%s)",
                    error)
                sys.exit(1)
            except DispatcherError, error:
                logger.critical("Sending failed. (%s)", error)
                break # End this run
            except Exception, error:
                logger.exception("Unknown exception: %s", error)

            logger.info("SMS sent to %s.", user)

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

def signalhandler(signum, _):
    """
    Signal handler to close and reopen log file(s) on HUP.
    """

    if signum == signal.SIGHUP:
        global logger
        logger.info("SIGHUP received; reopening log files.")
        nav.logs.reopen_log_files()
        logger.info("Log files reopened.")

def getconfig(defaults = None):
    """
    Read whole config from file.

    Arguments:
        ``defaults'' are passed on to configparser before reading config.

    Returns:
        Returns a dict, with sections names as keys and a dict for each
        section as values.
    """

    config = ConfigParser.RawConfigParser(defaults)
    config.read(configfile)

    sections = config.sections()
    configdict = {}

    for section in sections:
        configsection = config.items(section)
        sectiondict = {}
        for opt, val in configsection:
            sectiondict[opt] = val
        configdict[section] = sectiondict

    return configdict

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

def setdelay(sec):
    """Set delay (in seconds) between queue checks."""

    global delay, logger

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

