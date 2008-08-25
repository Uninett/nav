#!/usr/bin/python

import sys
import os
import getopt
import getpass
import tempfile
from xmlrpclib import ServerProxy


# Config

lp_xmlrpc_url = "xmlrpc.launchpad.net/bugs/"


# No need to edit anything below this

username = None
password = None

opts, args = getopt.getopt(sys.argv[1:], "t:s:u:h", ["title", "summary", "username", "help"])

title = None
summary = None
user_by_cmd = None
for opt, arg in opts:
    if opt in ("-t", "--title"):
        title = arg
    if opt in ("-s", "--summary"):
        summary = arg
    if opt in ("-u", "--username"):
        username = arg
        username_by_cmd = True
    if opt in ("-h", "--help"):
        print "NAV-bug  -- Helping you report nav-bugs since 1970"
        print "--------------------------------------------------"
        print " Options:"
        print " -t / --title  : Assigns a title to the bug (required)"
        print " -s / --summary: The bugreport. Opens $EDITOR if not given (vim if $EDITOR is not set)"
        print " -u / --username: Specify the launchpad username to be used"
        print ""
        print "Username and password can be stored in ~/.nav_bugs.conf"
        print "Example:"
        print "user=myusername"
        print "pass=mypassword"
        print ""
        sys.exit(0)

if not title:
    print "You must supply a title with the -t option"
    sys.exit(1)

config = None
try:
    config = open("%s/.nav_bugs.conf" % os.path.expanduser('~'))
except IOError:
    if not username:
        print "Error: Could not open ~/.nav_bugs.conf and no username given by the -u operator"
        sys.exit(1)

if config:
    for line in config.readlines():
        if line.startswith("user="):
            if not username:
                username = line[5:line.rfind('\n')]
        elif line.startswith("pass="):
            password = line[5:line.rfind('\n')]

if not username:
    print "Couldn't find username in commandline options or in config-file. Exiting"
    sys.exit(1)

if not password or username_by_cmd:
    password = getpass.getpass()

if not summary:
    tempfile = tempfile.mktemp('','nav_bug-')
    ret = os.system("%s %s" % (os.environ.get('EDITOR', 'vim'), tempfile))
    if ret != 0:
        print "vim did returned non-zero returncode. exiting"
        sys.exit(1)
    try:
        summary_file = open("%s" % tempfile)
        summary = "".join(summary_file.readlines())
    except IOError:
        print "File not saved from editor. exiting"
        sys.exit(1)

    os.remove("%s" % tempfile)

    if not summary or summary == "":
        print "Empty summary. exiting"
        sys.exit(1)


# Connect to launchpad
server = ServerProxy("https://%s:%s@%s" % (username, password, lp_xmlrpc_url))

url = server.filebug(dict(
    product='nav',
    title=title,
    summary=title,
    comment=summary))

print "Reported bug. Have a look at ", url

