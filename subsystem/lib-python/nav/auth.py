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
import logging

logger = logging.getLogger('nav.auth')

ADMINGROUP = 1
ANONYMOUSGROUP = 2
AUTHENTICATEDGROUP = 3

def hasPrivilege(user, action, target):
    """
    Magically resolves whether 'user' has been granted privileges to
    perform 'action' on 'target'.  The user parameter may be either
    None or an instance of nav.db.navprofiles.Account (e.g. taken from
    req.session['user'])
    """
    if type(user) is navprofiles.Account:
        # Verify that the account object already has cached privilege
        # data; cache them if not.
        try:
            user._privDict
        except:
            user.cachePrivileges()
        privileges = user._privDict
        groupIds = user._groupList
    elif not user:
        privileges = {}
        groupIds = []
    else:
        raise "user parameter is of invalid type %s" % type(user)

    # If user is a member of the Administrators group, we grant
    # him/her any privilege asked for.
    if ADMINGROUP in groupIds:
        return True

    # We don't match the target directly, since this may be open to
    # interpretation based on what the action is.  E.g. if the
    # action is 'web_access', we must treat the registered targets
    # as regular expressions to match against the target that was
    # asked for.
    # If we know an action needs tailored parsing of the target
    # attribute, we provide for that here.  Anything unknown is
    # matched as plaintext.
    if action == 'web_access' and action in privileges:
        return _matchRegexpTarget(target, privileges[action])
    else:
        return action in privileges and target in privileges[action]

def _matchRegexpTarget(target, regexpList):
    """Run through a list of regexp expressions and return true if
    the target matches any of the regexps in the privilege rows.
    """
    for r in regexpList:
        regexp = re.compile(r)
        if regexp.search(target):
            return True
        else:
            logger.debug("_matchRegexpTarget: %s did not match %s" % \
                         (repr(target), repr(r)))

    return False

def cachePrivileges(account):
    """Load and cache from the database all privileges associated
    with this account"""
    from nav.db import navprofiles

    groups = account.getChildren(navprofiles.Accountingroup)
    groupIds = [int(group.group) for group in groups]

    # FIMXE these are no longer needed due to db insert trigger
    # Make sure the user is always considered a member of the
    # Anonymous group.
    if ANONYMOUSGROUP not in groupIds: groupIds.append(ANONYMOUSGROUP)
    # Make sure an authenticated user is always considered a member
    # of the "Authenticated users" group
    if account.id > 0: groupIds.append(AUTHENTICATEDGROUP)

    groupString = ','.join([str(id) for id in groupIds])
    sql = """SELECT DISTINCT action, target
             FROM privilegebygroup
             WHERE accountgroupid IN (%s)""" % (groupString)
    cursor = account.cursor()
    cursor.execute(sql)

    # Create a dictionary of privileges
    privDict = {}
    for action, target in cursor.fetchall():
        if action not in privDict:
            privDict[action] = []
        privDict[action].append(target)

    # Cache both the privilege dictionary and the group id list in
    # the account object
    account._groupList = groupIds
    account._privDict = privDict

try:
    navprofiles.Account.cachePrivileges
except:
    navprofiles.Account.cachePrivileges = cachePrivileges
