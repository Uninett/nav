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

  -h,   --help      -- Show this help text
  -c,   --cancel    -- Cancel (mark as ignored) all unsent messages
  -d,   --delay     -- Set delay (in seconds) between queue checks
  -t,   --test      -- Send a test message to <phone no.>
"""

__copyright__ = "Copyright 2006 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus@jodal.no)"
__id__ = "$Id:$"

import sys
import os
import os.path
import getopt

try:
    import nav.path
except:
    # If the path module was not found, just pick default directories
    # below CWD
    LOCALSTATEDIR = '/usr/local/nav/var'
else:
    LOCALSTATEDIR = nav.path.localstatedir


### WORKFLOW (modeled after the old smsd.pl)
#
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
#       Sleep 60s (.pl legacy. Why do we do sleep before the next user?)
#   Get unsent messages from queue (.pl lagacy. This is redundant!)
#   Sleep $delay
# Loop end
# Exit

def main(args):
    if len(args) == 0:
        usage()
        sys.exit(1)
    raise "Not Implemented"

### INIT FUNCTIONS
#
# Switch user to navcron (will only work if we are running as root)
#   If navcron user exists
#       Change user to navcron (remember to change groups too)
#       If failed
#           Die "unable to change uid"
#   Else
#       Error 
#
# Check if already running
#   If pid file
#       If corrupt pid file
#           Die with error (which is caught by cron and mailed?)
#       Get pid
#       Send SIGNAL 0 to proccess with $pid
#       If alive
#           Bail out and die nicely
#   Else
#       Do nothing (in other words, the startup process continues)
#
# Get DB connection (imported)
#
# Demonize (is it reasonable to have a function for this?)
#   Release STDIN, STDOUT, STDERR
#   Move to the background as a deaemon
#   Write pid to pid file

def usage():
    """Print a usage screen to stderr."""
    print >> sys.stderr, __doc__


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
#   


### COMMON FUNCTIONS (eg. should be general and imported from somewhere)
#
# Send mail
#   Get address, subject and body from args
#   Send mail
#
# Log
#   Get message from args
#   Write message to log
#
# Error
#   Get message from args
#   Log message
#   Send mail to error (system-wide?) contact with message


### Dispatcher plugins
# FIXME: Move the plugin classes into modules

class GammuDispatcher(object):
    """The Gammu dispatcher plugin."""
    def __init__(self, file):
        raise "Not Implemented"

### Begin program
main(sys.argv[1:])
