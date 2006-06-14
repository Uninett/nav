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

"""The NAV SMS daemon (smsd)

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

import sys
import os
import pwd
import grp
import getopt
import email
import smtplib
import logging  # requires Python >= 2.3
import socket

import nav.config
import nav.db
import nav.path

### VARIABLES

delay = 30 # Change at run-time with --delay
username = 'navcron'
pidfile = nav.path.localstatedir + '/run/smsd.py.pid'
logfile = nav.path.localstatedir + '/log/smsd.py.log'
loglevel = logging.DEBUG
mailwarnlevel = logging.ERROR
adminmail = nav.config.readConfig('nav.conf')['ADMIN_MAIL']
adminmail = 'jodal@localhost' # for devel

### WORKFLOW (modeled after the old smsd.pl)
#
# Get command line arguments
# Switch user to navcron
# Check if already running
# Get DB connection
# Act upon command line arguments
#   Help
#   Ignore all unsent messagesa (-c, --cancel)
#   Test (-t, --test)
#       Format SMS
#       Send SMS
#   Set $delay (-d, --delay)
# Daemonize
# Loop forever
#   Get unsent messages from queue
#   Sort messages by cell number
#   Loop over users (one cell number == one user)
#       Get all unsent messages for a user
#       Format SMS
#       Send SMS
#   Sleep $delay
# Loop end
# Exit

def main(args):
    # Get command line arguments
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
            print "'--cancel' not implemented" # FIXME
        if opt in ('-d', '--delay'):
            setdelay(val)
        if opt in ('-t', '--test'):
            print "'--test' not implemented" # FIXME

    # Switch user to navcron
    switchuser(username)

    # Check if already running
    justme()

    # Get DB connection
    dbconn = nav.db.getConnection('navprofile')

    # Act upon command line arguments
    pass # FIXME

    # Daemonize
    pass # FIXME

    # Loop forever
    pass # FIXME

    # Exit
    sys.exit(0)


### COMMON FUNCTIONS (functions we may want to move to the NAV API)

def sendmail(to, subject, body):
    """Send mail with subject and body to recipient.

    Pseudo code:
    Get addresses, subject and body from args and system
    Connect to SMTP server
    Send mail
    Close SMTP connection"""

    localuser = pwd.getpwuid(os.getuid())[0] 
    hostname = socket.gethostname()
    sender = localuser + '@' + hostname

    headers = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % \
     (sender, to, subject)
    message = headers + body

    try:
        server = smtplib.SMTP('localhost')
        server.sendmail(sender, to, message)
        server.quit()
    except Exception, error:
        log("Failed to send mail. (%s)" % error, logging.ERROR)

def log(msg, level = logging.NOTSET, destination = 'file'):
    """Write message to log.
    
    level can be any of NOTSET, DEBUG, INFO, WARNING, ERROR, and CRITICAL, in
    order of increasing importance. Default is NOTSET.
    
    destination supports 'file' for logging to logfiles, and 'console' for
    logging to console/stderr. Default is 'file'."""

    global logfile, loglevel

    # Get a log
    logging.basicConfig() # Does not take arguments in Python < 2.4
    logger = logging.getLogger('smsd')

    if destination == 'file':
        # Log to file
        try:
            handler = logging.FileHandler(logfile, 'a')
        except IOError, error:
            print >> sys.stderr, \
             "Failed writing to logfile. Exiting. (%s)" % error
            sys.exit(error.errno)
        format = '%(asctime)s %(levelname)-8s %(message)s'
    elif destination == 'console':
        # Log to console/stderr
        try:
            handler = logging.StreamHandler(sys.stderr)
        except IOError, error:
            print >> sys.stderr, \
             "Failed writing to stderr. Exiting. (%s)" % error
            sys.exit(error.errno)
        format = '%(levelname)s %(message)s'

    # Set a log format
    formatter = logging.Formatter(format)

    # Connect the pieces
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(loglevel)

    # Log the message
    logger.log(level, msg)
    # FIXME: Default format ouput is coming to console for all destinations in
    # addition to going to the right place in the right format

def reportError(msg, level = logging.NOTSET, destination = 'file'):
    """Log and mail error message.

    Pseudo code:
    Get message from args
    Log message
    Send mail to admin with message"""

    global adminmail, mailwarnlevel

    # Pass on for logging
    log(msg, level, destination)

    # Notify admin by mail
    # FIXME: Replace with logging.SMTPHandler ... <3 logging <3
    if adminmail is not False and level >= mailwarnlevel:
        # FIXME: More info in the msg?
        sendmail(adminmail, 'NAV SMS daemon error report', msg)

# Demonize
#   Release STDIN, STDOUT, STDERR
#   Move to the background as a deaemon
#   Write pid to pid file



### INIT FUNCTIONS

def usergroups(username):
    """Find all non-primary groups an user is member of."""
    
    gids = []
    for (name, passwd, gid, members) in grp.getgrall():
        if username in members:
            gids.append(gid)
    return gids

def switchuser(username):
    """Switch user the process is running as to given username, normally 'navcron'.

    Will only work if we are running as root.

    Pseudo code:
    If navcron user exists
        Change user to navcron
        Change groups to navcron's groups
        If failed
            Die "unable to change uid/gids"
    Else
        Error"""

    olduid = os.getuid()
    oldgid = os.getgid()

    try:
        name, passwd, uid, gid, gecos, dir, shell = pwd.getpwnam(username)
    except KeyError, error:
        reportError("User %s not found. Running as root! (%s)" % \
         (username, error), logging.WARNING, 'console')
    else:
        if olduid != uid:
            try:
                os.setgid(gid)
                gids = usergroups(username)
                if len(gids) > 0:
                    os.setgroups(gids)
                os.setuid(uid)
            except OSError, error:
                reportError("Failed changing uid/gid from %d/%d to %d/%d. (%s)" % \
                 (olduid, oldgid, uid, gid, error), \
                 logging.ERROR, 'console')
                sys.exit(error.errno)
            else:
                reportError("uid/gid successfully changed from %d/%d to %d/%d." \
                 % (olduid, oldgid, uid, gid), logging.INFO)
        else:
            reportError("Already running as uid/gid %d/%d." \
             % (olduid, oldgid), logging.INFO)

def justme():
    """Check if already running.

    Pseudo code:
    If pid file
        If corrupt pid file
            Die with error (which is caught by e.g. startstop.py)
        Get pid from file
        Send SIGNAL 0 to proccess with $pid
        If alive
            Bail out and die nicely
    Else
        Do nothing (in other words, the startup process continues)"""

    global pidfile
    if os.access(pidfile, os.R_OK):
        fd = file(pidfile, 'r')
        pid = fd.readline()
        fd.close()

        if pid.isdigit():
            pid = int(pid) 
        else:
            reportError("Can't read pid from pid file " + pidfile \
             + ". Don't know if process is already running, thus bailing out.", \
             logging.ERROR, 'console')
            sys.exit(1)

        try:
            os.kill(pid, 0) # Sending signal 0 to check if process is alive
        except OSError, error:
            # Normally "No such process", and thus we continue
            pass
        else:
            # We assume the process lives and bails out
            reportError("%s already running (pid %d), bailing out." % \
             (sys.argv[0], pid), logging.ERROR, 'console')
            sys.exit(1)
    else:
        pass # No pidfile, assume we're alone and continue


# Command line argument processing

def usage():
    """Print a usage screen to stderr."""
    print >> sys.stderr, __doc__

def setdelay(sec):
    """Set delay (in seconds) between queue checks."""
    global delay
    if sec.isdigit():
        delay = int(sec)
    else:
        reportError("Given delay not a digit. Using default.", \
         logging.WARNING, 'console')
    

### LOOP FUNCTIONS
#
# Check DB connection
#   If connection
#       Do nothing
#   Else
#       Get error message
#       Log error message
#       Mail error message
#
# Get unsent messages from queue
#   Check DB connection
#   Get messages from DB where status = 'N'
#
# Format SMS (dispatcher may need to be known before formatting)
#   If one message
#       SMS = message
#   If multiple messages
#       SMS = as many msgs as possible + how many was ignored
#
# Send SMS
#   Which dispatcher do we want to use? Integration with profiles?
#   Send SMS using dispatcher
#   If sending successfull
#       Mark as sent/ignored, with timestamp, in DB
#       Log
#   Else
#       Error (log and mail)


### Dispatcher plugins
# FIXME: Move the plugin classes into modules

class GammuDispatcher(object):
    """The Gammu dispatcher plugin."""
    def __init__(self, file):
        raise "Not Implemented"

### Begin program
main(sys.argv[1:])
