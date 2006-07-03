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
import ConfigParser # parts require Python >= 2.3
import email
import grp
import getopt
import logging # require Python >= 2.3
import logging.handlers # require Python >= 2.3
import os
import pwd
import smtplib
import socket
import sys
import time

import nav.config
import nav.daemon
import nav.path
import nav.smsd.navdbqueue
from nav.smsd.dispatcher import DispatcherError
# Dispatchers are imported later according to config


### PATHS

configfile = nav.path.sysconfdir + '/smsd.conf'
logfile = nav.path.localstatedir + '/log/smsd.log'
pidfile = nav.path.localstatedir + '/run/smsd.pid'


### MAIN FUNCTION

def main(args):
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
    config = getconfig(defaults)

    # Set variables
    username = config['main']['username']
    delay = int(config['main']['delay'])
    loglevel = eval('logging.' + config['main']['loglevel'])
    mailwarnlevel = eval('logging.' + config['main']['mailwarnlevel'])
    mailserver = config['main']['mailserver']
    mailaddr = config['main']['mailaddr']

    # Initialize logger
    global logger
    logger = loginit('nav.smsd', logfile, loglevel, mailaddr, mailserver,
     mailwarnlevel)
    logger.info("-- smsd started --")

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
            opttest = val

    # Switch user to navcron
    nav.daemon.switchuser(username)

    # Ignore unsent messages
    if optcancel:
        queue = nav.smsd.navdbqueue.NAVDBQueue()
        ignCount = queue.cancel()
        logger.info("All %d unsent messages ignored.", ignCount)
        sys.exit(0)

    # Let the dispatcherhandler take care of our dispatchers
    dh = nav.smsd.dispatcher.DispatcherHandler(config)
    
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

    # Check if already running
    nav.daemon.justme(pidfile)

    # Daemonize
    nav.daemon.daemonize(pidfile)

    # Initialize queue
    # Note: If we're initalizing a queue with a DB connection before
    # daemonizing we've experienced that the daemon dies silently upon trying
    # to use the DB connection after becoming a daemon
    queue = nav.smsd.navdbqueue.NAVDBQueue()

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
            logger.info("Found %d unsent message(s) for %s.",
             len(msgs), user)

            # Dispatcher: Format and send SMS
            try:
                (sms, sent, ignored, smsid) = dh.sendsms(user, msgs)
            except DispatcherError, error:
                logger.critical("Sending failed. Exiting. (%s)", error)
                sys.exit(1)

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


### INIT FUNCTIONS

def getconfig(defaults = None):
    """
    Read whole config from file.
    
    Arguments:
        ``defaults'' are passed on to configparser before reading config.
    
    Returns:
        Returns a dict, with sections names as keys and a dict for each
        section as values.
    """

    config = ConfigParser.SafeConfigParser(defaults)
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

    # localuser will be root if smsd was started as root, since switchuser() is
    # first called at a later time
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


### BEGIN
if __name__ == '__main__':
    main(sys.argv[1:])

