"""
$Id$

This file is part of the NAV project.

Provides simple authorization API for NAV.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
from nav.db import navprofiles
import re
from nav import ip

ADMINGROUP = 1
ANONYMOUSGROUP = 2

_orgPrivs = ['org_access']

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
    elif action in _orgPrivs:
        return _hasOrgPrivileges(user, target)
    else:
        return _matchBasicTarget(target, privileges)

def _hasOrgPrivileges(user, target):
    """
    Determine whether the user has organizational privileges to the
    given target, usually an IP address or range/prefix.
    """
    from nav import db
    from nav.db import navprofiles
    from nav.db import manage

    targetAddr = ip.IPv4(target)
    conn = db.getConnection('webfront', 'manage')
    manageCursor = conn.cursor()

    # First, get the organizational units this user has an explicit or
    # implicit membership in.
    orgList = user.getImplicitOrgIds()
    
    if len(orgList) > 0:
        # Now we deduce which vlans, and therefrom which subnet prefixes,
        # belong to this set of organizations.
        orgString = ",".join(["'%s'" % org for org in orgList])
        sql = \
            """
            SELECT DISTINCT b.netaddr
            FROM vlan a, prefix b
            WHERE a.vlan=b.vlan
            AND a.orgid IN (%s);
            """ % orgString
        manageCursor.execute(sql)

        # Walk through each prefix (netaddr) and check whether the target
        # is contained in it.
        prefixes = manageCursor.dictfetchall()
        for prefix in prefixes:
            net = ip.IPv4(prefix['netaddr'])
            if targetAddr in net:
                return True
    return False
    
def _matchBasicTarget(target, dictList):
    """
    Run through a list of rows from a privilege search and return
    true if plaintext target exists among the privilege rows.
    """
    for row in dictList:
        if row['target'] == target:
            return True
    return False

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
