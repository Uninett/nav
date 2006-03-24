# -*- coding: ISO8859-1 -*-
#
# Copyright 2003, 2004 Norwegian University of Science and Technology
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
#
# $Id$
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#
"""
Provides simple authorization API for NAV.
"""
from nav.db import navprofiles
import re

ADMINGROUP = 1
ANONYMOUSGROUP = 2

def hasPrivilege(user, action, target):
    """
    Magically resolves whether 'user' has been granted privileges to
    perform 'action' on 'target'.  The user parameter may be either
    None or an instance of nav.db.navprofiles.Account (e.g. taken from
    req.session['user'])
    """

    if type(user) is navprofiles.Account:
        # Get list of user's group memberships
        links = user.getChildren(navprofiles.Accountingroup)
        groupIds = [int(link.group) for link in links]
    elif not user:
        groupIds = []
    else:
        raise "user parameter is of invalid type %s" % type(user)

    # Make sure the user is always considered a member of the
    # Anonymous group.
    if not ANONYMOUSGROUP in groupIds:
        groupIds.append(ANONYMOUSGROUP)

    # If user is a member of the Administrators group, we grant
    # him/her whatever privilege is asked for.
    if ADMINGROUP in groupIds:
        return True

    # Construct and execute an SQL statement to retrieve any rows
    # matching the named privilege (action) for this user's
    # groups. We don't match the target directly, since this may
    # be open to interpretation based on what the action is.
    # E.g. if the action is 'web_access', we must treat the
    # registered targets as regular expressions to match against
    # the target that was asked for.
    groupString = ','.join([str(id) for id in groupIds])
    sql = """
    SELECT *
    FROM PrivilegeByGroup
    WHERE accountgroupid IN (%s)
          AND action = '%s'
    """ % (groupString, action)
    cursor = navprofiles.Account.cursor()
    cursor.execute(sql)

    privileges = cursor.dictfetchall()

    # If we know an action needs tailored parsing of the target
    # attribute, we provide for that here.  Anything unknown is
    # matched as plaintext.
    if action == 'web_access':
        return _matchRegexpTarget(target, privileges)
    else:
        return _matchBasicTarget(target, privileges)

def _matchRegexpTarget(target, dictList):
    """
    Run through a list of rows from a privilege search and return
    true if the target matches any of the regexps in the privilege rows.
    """
    for row in dictList:
        regexp = re.compile(row['target'])
        if regexp.search(target):
            return True
    return False
