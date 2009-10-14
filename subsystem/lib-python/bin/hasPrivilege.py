#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
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
This script determines whether a NAV user has been granted a specific
privilege.
"""
import sys, getopt
import nav, nav.auth
from nav import db
from nav.db import navprofiles
from nav.db.navprofiles import Account


def main(args):
    (opts, args) = getopt.getopt(args, 'h', ['help'])

    for (switch, arg) in opts:
        if switch in ('-h', '--help'):
            usage()
            sys.exit(10)

    if len(args) < 3:
        print >> sys.stderr, "Not enough parameters, see help screen."
        sys.exit(10)

    (user, privilege, target) = args[:3]

    # Make sure we have a proper database connection
    try:
        conn = db.getConnection('navprofile', 'navprofile')
        cursor = conn.cursor()
    except Exception, error:
        print >> sys.stderr, "There was an error connecting to the database"
        sys.exit(10)

    # Make sure the specified login name has an existing account
    try:
        account = Account.loadByLogin(user)
    except Exception, error:
        print >> sys.stderr, "Could not find user '%s'" % user
        sys.exit(10)
        
    # Make use of the privilege system to discover whether the user
    # has been granted the privilege that is being asked for
    try:
        answer = nav.auth.hasPrivilege(account, privilege, target)
    except Exception, error:
        print >> sys.stderr, "There was an error when asking for the privilege"
        sys.exit(10)

    if answer:
        sys.exit(0)
    else:
        sys.exit(1)
    
def usage():
    print >> sys.stderr, """Determine whether a NAV user has been granted a specific privilege.
Mostly for internal NAV usage.

Usage:  hasPrivilege.py subject action target

  subject  - The login name of the user that requests the privilege
  action   - The name of the privilege requested
  target   - Specification of that the privilege is requested for

Exit codes:
  If the privilege was granted, the return code is 0.  If not, the
  return code is 1.
  If the script encountered errors during privilege checking, the
  return code will be > 1.

Example: hasPrivilege.py admin web_access /useradmin/index
"""

##############################
# main execution begins here #
##############################

main(sys.argv[1:])
