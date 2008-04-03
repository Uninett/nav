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
This module represents the useradmin pages of the NAV web interface.
It follows the mod_python.publisher paradigm.
"""
#from mod_python import apache
import os, nav, psycopg, forgetSQL
from nav import web, db
from nav.db import navprofiles, manage
from nav.web.templates.useradmin import *

def _profileCursor():
    _profileConn = db.getConnection('navprofile', 'navprofile')
    return _profileConn.cursor()

def _manageCursor():
    _manageConn = db.getConnection('webfront', 'manage')
    return _manageConn.cursor()

def _accountsToTemplate(accounts):
    """Convert a list of Account objects into a list of dictionaries
    containing the Account properties."""
    accountList = [{'id': item.id,
                    'login': item.login,
                    'name': item.name,
                    'ext_sync': item.ext_sync,
                    'groupcount': len(item.getGroups())
                    } for item in accounts ]
    return accountList

def _groupsToTemplate(groups):
    """Convert a list of Account objects into a list of dictionaries
    containing the Account properties."""
    groupList = [{'id': item.id,
                  'name': item.name,
                  'description': item.descr,
                  'membercount': len(item.getMembers())
                  } for item in groups ]
    return groupList

def _getAccounts(includeIds=[], excludeIds=[]):
    """Return a list of rows from the Account table"""
    criteria = []
    if len(includeIds) > 0:
        criteria.append("id IN (%s)" % ','.join([str(x) for x in includeIds]))
    if len(excludeIds) > 0:
        criteria.append("id NOT IN (%s)" % ','.join([str(x) for x in excludeIds]))

    if len(criteria) > 0:
        accounts = navprofiles.Account.getAll(where=criteria, orderBy="login")
    else:
        accounts = navprofiles.Account.getAll(orderBy="login")
    return _accountsToTemplate(accounts)

def _getGroups(includeIds=[], excludeIds=[]):
    """Return a list of rows from the AccountGroup table"""
    criteria = []
    if len(includeIds) > 0:
        criteria.append("id IN (%s)" % ','.join([str(x) for x in includeIds]))
    if len(excludeIds) > 0:
        criteria.append("id NOT IN (%s)" % ','.join([str(x) for x in excludeIds]))

    if len(criteria) > 0:
        groups = navprofiles.Accountgroup.getAll(where=criteria, orderBy="name")
    else:
        groups = navprofiles.Accountgroup.getAll(orderBy="name")
    return _groupsToTemplate(groups)

def _accountExists(id):
    cursor = _profileCursor()
    sql = \
        """SELECT COUNT(id)
        FROM Account
        WHERE id=%d""" % id
    cursor.execute(sql)
    return cursor.fetchone()[0] > 0

def _groupExists(id):
    cursor = _profileCursor()
    sql = \
        """SELECT COUNT(id)
        FROM AccountGroup
        WHERE id=%d""" % id
    cursor.execute(sql)
    return cursor.fetchone()[0] > 0

def _link(uid, gid):
    """Links an account and a group in the AccountInGroup table"""
    cursor = _profileCursor()
    sql = \
        """INSERT INTO AccountInGroup
        (accountid, groupid)
        VALUES
        (%d, %d)""" % (uid, gid)
    try:
        cursor.execute(sql)
        return True
    except psycopg.IntegrityError:
        # They were already linked, or at least one of the id's are
        # non-existant.
        return False

def _unlink(uid, gid):
    """Unlinks an account and a group in the AccountInGroup table"""
    cursor = _profileCursor()
    sql = \
        """DELETE FROM AccountInGroup
        WHERE accountid=%d
          AND groupid=%d""" % (uid, gid)
    cursor.execute(sql)
    return True

def _linkOp(req, uid, gid, source, linkFunc, success, failure):
    """Contains the common code for performing a link or unlink
    operation. The linkFunc parameter should refer to either the
    _link() or _unlink() function.  """
    # Sanitary work on arguments
    try:
        uid = int(uid)
        gid = int(gid)
    except TypeError:
        return "Invalid arguments"
    if source is not None and source not in ('group', 'account'):
        return "Invalid arguments"

    if not _accountExists(uid):
        return "no such account %d" % uid
    elif not _groupExists(gid):
        return "no such group %d" % gid

    if linkFunc(uid, gid):
        if source:
            if source == 'group':
                web.redirect(req, "group?id=%d" % gid)
            elif source == 'account':
                web.redirect(req, "account?id=%d" % uid)
        else:
            return success
    else:
        return failure

def _getPrivileges():
    """Return a dictionary of valid privilege names, using their id
    numbers as key."""
    cursor = _profileCursor()
    sql = \
        """SELECT *
        FROM Privilege"""
    cursor.execute(sql)
    rows = cursor.dictfetchall()

    structure = {}
    for row in rows:
        structure[ row['privilegeid'] ] = row['privilegename']
    return structure

def _getGroupPrivileges(gid):
    """Return a list of dictionaries containing the privilege specs
    for a given group id.  This will probably only work as long as we
    store the privileges specs in our own SQL database."""
    cursor = _profileCursor()
    sql = \
        """SELECT *
        FROM AccountGroupPrivilege
        INNER JOIN Privilege USING (privilegeid)
        WHERE accountgroupid=%d
        ORDER BY privilegename, target""" % gid
    cursor.execute(sql)
    return cursor.dictfetchall()

def _getPrivileges():
    """Return a list of dictionaries containing valid privilege names
    and their id numbers"""
    privileges = navprofiles.Privilege.getAll(orderBy="privilegename")
    return privileges

def _getNextSequence(sequence):
    cursor = _profileCursor()
    sql = \
        """SELECT nextval('%s'::text)""" % sequence
    cursor.execute(sql)
    row = cursor.fetchone()
    return row[0]

def _storeGroup(groupStruct):
    """Takes a group structure and attempts to store in in the
    database.  If the supplied group structure contains an id number,
    this is considered an update of an existing record, else it is
    considered a new group."""
    cursor = _profileCursor()

    newRecord = not groupStruct.has_key('id') \
                or groupStruct['id'] is None \
                or groupStruct['id'].strip() == ""
    if newRecord:
        id = _getNextSequence('accountgroupids')
        values = [str(id), groupStruct['name'], groupStruct['description']]
        escapedValues = [ nav.db.escape(v) for v in values ]
        valueStr = ",".join(escapedValues)
        sql = \
            """INSERT INTO AccountGroup
            (id, name, descr)
            VALUES
            (%s)""" % valueStr
        cursor.execute(sql)
        return True
    else:
        id = groupStruct['id']
        values = [groupStruct['name'], groupStruct['description']]
        sql = \
            """UPDATE AccountGroup
            SET name=%s, descr=%s
            WHERE id=%s""" % (
                nav.db.escape(groupStruct['name']),
                nav.db.escape(groupStruct['description']),
                int(id))
        cursor.execute(sql)
        return True

def _storeAccount(accountStruct):
    """Takes an account structure and attempts to store in in the
    database.  If the supplied account structure contains an id number,
    this is considered an update of an existing record, else it is
    considered a new account."""
    cursor = _profileCursor()

    newRecord = not accountStruct.has_key('id') \
                or accountStruct['id'] is None \
                or accountStruct['id'].strip() == ""
    if newRecord:
        id = _getNextSequence('accountids')
        values = [str(id), accountStruct['login'],
                  accountStruct['name'],
                  accountStruct['password']]
        escapedValues = [ nav.db.escape(v) for v in values ]
        valueStr = ",".join(escapedValues)
        sql = \
            """INSERT INTO Account
            (id, login, name, password)
            VALUES
            (%s)""" % valueStr
        cursor.execute(sql)
        return True
    else:
        id = accountStruct['id']
        values = [accountStruct['login'],
                  accountStruct['name'],
                  accountStruct['password']]
        sql = \
            """UPDATE Account
            SET login=%s, name=%s, password=%s
            WHERE id=%s""" % (
                nav.db.escape(accountStruct['login']),
                nav.db.escape(accountStruct['name']),
                nav.db.escape(accountStruct['password']),
                int(id))
        cursor.execute(sql)
        return True


###                                 ###
### Public web functions begin here ###
###                                 ###

def accountlist(req):
    """Display a list of the accounts registered within NAV."""
    page = AccountList()
    page.accounts = _getAccounts()
    page.path[-1] = ("Account list", False)
    page.title = "Account list"
    page.current = "accountlist"

    if req.session.has_key('statusMessage'):
        page.statusMessage = req.session['statusMessage']
        del req.session['statusMessage']

    return page

def grouplist(req):
    """Display a list of the groups registered within NAV."""
    page = GroupList()
    page.groups = _getGroups()
    page.path[-1] = ("Group list", False)
    page.title = "Group list"
    page.current = "grouplist"

    if req.session.has_key('statusMessage'):
        page.statusMessage = req.session['statusMessage']
        del req.session['statusMessage']

    return page

def account(req, id=None):
    """Display all relevant data about an Account in an editable form."""
    page = AccountPage()
    page.path[-1] = ("Edit account", False)
    if id is not None:
        # Sanitary work on arguments
        try:
            id = int(id)
        except TypeError:
            return "%s is not a valid account id" % repr(id)

        account = navprofiles.Account(id)
        try:
            account.load()
        except forgetSQL.NotFound:
            return "no such account %s" % id

        page.newAccount = False
        page.information = "Editing account \"%s\" (#%s)" % (account.name, account.id)
        page.account = _accountsToTemplate([account])[0]
        page.editable = account.ext_sync is None or account.ext_sync == ''
        page.account['groups'] = _groupsToTemplate(account.getGroups())
        page.account['organizations'] = account.getOrgIds()
        page.account['organizations'].sort()
    else:
        page.newAccount = True
        page.information = "Creating new account"
        page.account = {'id': None,
                        'login': '',
                        'name': 'New user',
                        'ext_sync': None,
                        'groups': []}
        page.editable = True
        
    page.title = page.information
    page.current = "account"
    # We've filled out most of the details of the account and its
    # group memberships, now we need to fill out the list of groups it
    # has no membership to so that we may add the account to any of
    # these
    groupIds = [ group['id'] for group in page.account['groups'] ]
    page.account['nongroups'] = _getGroups(excludeIds=groupIds)
    page.orgTree = manage.getOrgTree()

    if req.session.has_key('statusMessage'):
        page.statusMessage = req.session['statusMessage']
        del req.session['statusMessage']

    return page

def group(req, id=None):
    """Display all relevant data about an Account in an editable form"""
    # Sanitary work on arguments
    page = GroupPage()
    page.path[-1] = ("Edit group", False)
    if id is not None:
        try:
            id = int(id)
        except TypeError:
            return "%s is not a valid group id" % repr(id)

        group = navprofiles.Accountgroup(id)
        try:
            group.load()
        except forgetSQL.NotFound:
            return "no such group %s" % id

        page.newGroup = False
        page.information = "Editing group \"%s\" (#%s)" % (group.name, group.id)
        page.group = _groupsToTemplate([group])[0]
        page.editable = True
        page.group['members'] = _accountsToTemplate(group.getMembers())
        page.group['privileges'] = _getGroupPrivileges(id)
    else:
        page.newGroup = True
        page.information = "Creating a new group"
        page.editable = True
        page.group = {'id': None,
                      'name': 'New group',
                      'description': 'New group',
                      'members': [],
                      'privileges': []}

    page.title = page.information
    page.current = "group"
    # We've filled out most of the details of the group and its
    # members, now we need to fill out the list of non-members so that
    # we may add new members to this group on this form.
    memberIds = [ member['id'] for member in page.group['members'] ]
    page.group['nonmembers'] = _getAccounts(excludeIds=memberIds)
    page.privileges = _getPrivileges()

    if req.session.has_key('statusMessage'):
        page.statusMessage = req.session['statusMessage']
        del req.session['statusMessage']
        req.session.save()

    return page

def link(req, uid=None, gid=None, source=None):
    """Associates an account and a group."""
    return _linkOp(req, uid, gid, source,
                   _link,
                   "Linked %s to %s" % (uid, gid),
                   "%s is already a member of %s" % (uid, gid)
                   )

def unlink(req, uid=None, gid=None, source=None):
    """Disassociates an account and a group."""
    return _linkOp(req, uid, gid, source,
                   _unlink,
                   "Unlinked %s from %s" % (uid, gid),
                   "Unlink failed"
                   )

def groupsubmit(req, id=None, name=None, description=None):
    """Receives and stores information submitted from the group
    form."""
    if id is not None:
        # We are attempting to submit data for an existing group
        redir = 'group?id=%s' % id
        try:
            id = int(id)
        except TypeError:
            return "%s is not a valid group id" % id

        group = navprofiles.Accountgroup(id)
        try:
            group.load()
        except forgetSQL.NotFound:
            return "Group id %s does not exist" % id
    else:
        redir = 'group'
        group = navprofiles.Accountgroup()

    if name != group.name:
        group.name = name
    if description != group.descr:
        group.descr = description

    try:
        group.save()
        redir = 'group?id=%s' % group.id
        req.session['statusMessage'] = "Group successfully stored"
    except psycopg.IntegrityError:
        req.session['statusMessage'] = "A database integrity error prevented us from storing the Group"

    web.redirect(req, redir, seeOther=True)

def accountsubmit(req, id=None, login=None, name=None, password=None, passwordConfirm=None):
    """Receives and stores information submitted from the account
    form."""
    if id is not None:
        # We are attempting to submit data for an existing account
        redir = 'account?id=%s' % id
        try:
            id = int(id)
        except TypeError:
            return "%s is not a valid account id" % id

        account = navprofiles.Account(id)
        try:
            account.load()
        except forgetSQL.NotFound:
            return "Account id %s does not exist" % id

    else:
        redir = 'account'
        account = navprofiles.Account()
    
    if password != passwordConfirm:
        req.session['statusMessage'] = "Passwords do not match"
        account.reset()
    elif login is None or len(login) == 0:
        req.session['statusMessage'] = "Login name was empty"
        account.reset()
    else:
        if login != account.login:
            account.login = login
        if name != account.name:
            account.name = name
        if password:
            account.setPassword(password)
            
        try:
            account.save()
        except psycopg.IntegrityError:
            req.session['statusMessage'] = "A database integrity error prevented us from storing the Account"
        else:
            redir = 'account?id=%s' % account.id
            req.session['statusMessage'] = "Account successfully stored"

    req.session.save()
    web.redirect(req, redir, seeOther=True)

def accountdel(req, id=None, confirm=False):
    """Delete an account and redirect to the account list"""
    try:
        id = int(id)
    except TypeError:
        return "%s is not a valid account id" % id

    account = navprofiles.Account(id)
    try:
        account.load()
        name = account.name
    except forgetSQL.NotFound:
        return "No such account id %s" % id

    if id < 1000:
        req.session['statusMessage'] = "System account '%s' (#%s) cannot be deleted" % (name, id)
        web.redirect(req, "account?id=%s" % id, seeOther=True)
    elif not confirm:
        page = ConfirmPage()
        page.path[-1] = ("Delete an account", False)
        page.title = "Delete an account"
        page.current = "account"
        page.confirmation = "You are about to delete the account '%s' (#%s).  Are you sure?" % (name, id)
        page.yestarget = "accountdel?id=%s&confirm=1" % id
        page.notarget = "account?id=%s" % id
        return page
    else:
        account.delete()
        req.session['statusMessage'] = "Account '%s' (#%s) successfully deleted" % (name, id)
        web.redirect(req, "accountlist", seeOther=True)

def groupdel(req, id=None, confirm=False):
    """Delete a group and redirect to the group list"""
    try:
        id = int(id)
    except TypeError:
        return "%s is not a valid account id" % id

    group = navprofiles.Accountgroup(id)
    try:
        group.load()
        name = group.name
    except forgetSQL.NotFound:
        return "No such group id %s" % id

    if id < 1000:
        req.session['statusMessage'] = "System group '%s' (#%s) cannot be deleted" % (name, id)
        web.redirect(req, "group?id=%s" % id, seeOther=True)
    elif not confirm:
        page = ConfirmPage()
        page.path[-1] = ("Delete a group", False)
        page.title = "Delete a group"
        page.current = "group"
        page.confirmation = "You are about to delete the group '%s' (#%s).  Are you sure?" % (name, id)
        page.yestarget = "groupdel?id=%s&confirm=1" % id
        page.notarget = "group?id=%s" % id
        return page
    else:
        group.delete()
        req.session['statusMessage'] = "Group '%s' (#%s) successfully deleted" % (name, id)
        web.redirect(req, "grouplist", seeOther=True)

def grant(req, gid=None, pid=None, target=None):
    """Grant a privilege to a group."""
    if pid is None:
        req.session['statusMessage'] = "You must select a privilege to grant first"
        web.redirect(req, "group?id=%s" % gid)
        
    try:
        gid = int(gid)
        pid = int(pid)
    except TypeError:
        return "Invalid arguments"
    if target is None:
        return "Missing target"

    group = navprofiles.Accountgroup(gid)
    try:
        group.load()
    except forgetSQL.NotFound:
        return "No such group id %s" % gid
    
    privilege = navprofiles.Privilege(pid)
    try:
        privilege.load()
    except forgetSQL.NotFound:
        return "No such privilege id %s" % pid

    privrow = navprofiles.Accountgroupprivilege()
    privrow.privilege = privilege.id
    privrow.accountgroup = group.id
    privrow.target = target
    try:
        if privrow.save():
            req.session['statusMessage'] = "Successfully granted privilege '%s' for '%s'" % (privilege.name, target)
        else:
            req.session['statusMessage'] = "Failed to grant privilege '%s' for '%s'" % (privilege.name, target)
    except psycopg.IntegrityError:
        req.session['statusMessage'] = "Privilege '%s' is already granted for '%s'" % (privilege.name, target)
    web.redirect(req, "group?id=%s" % gid)
    
def revoke(req, gid=None, pid=None, target=None):
    """Revoke a privilege from a group."""
    try:
        gid = int(gid)
        pid = int(pid)
    except TypeError:
        return "Invalid arguments"
    if target is None:
        return "Missing target"

    privrow = navprofiles.Accountgroupprivilege(gid, pid, target)
    try:
        privrow.load()
        privrow.delete()
        privilege = navprofiles.Privilege(pid)
        req.session['statusMessage'] = "Successfully revoked privilege '%s' for '%s'" % (privilege.name, target)
    except forgetSQL.NotFound:
        return "No such privilege has previously been granted"
    
    web.redirect(req, "group?id=%s" % gid)

def orglink(req, uid=None, orgid=None):
    """Add a user to one or more organizations"""
    # First, sanitize arguments
    if type(orgid) is str:
        orgid = [orgid]
    elif type(orgid) is not list:
        return "Invalid arguments"
    try:
        uid = int(uid)
    except TypeError:
        return "Invalid arguments"

    # Check the the account id is valid
    try:
        account = navprofiles.Account(uid)
        account.load()
    except forgetSQL.NotFound:
        return "No such account id %s" % uid

    # Check that all orgids are valid
    for id in orgid:
        org = manage.Org(id)
        try:
            org.load()
        except forgetSQL.NotFound:
            return "No such organization %s" % repr(id)

    # Then, make the user member of all organizations
    successful = []
    for id in orgid:
        link = navprofiles.Accountorg()
        link.account = uid
        link.orgid = id
        try:
            link.save()
            successful.append(id)
        except psycopg.IntegrityError:
            pass

    if len(successful) > 0:
        req.session['statusMessage'] = "Successfully added %s to the following organizations: %s" % (
            account.login, ",".join(successful))
    else:
        req.session['statusMessage'] = "%s was not added to any organizations" % account.login
    web.redirect(req, "account?id=%s" % uid, seeOther=True)
    

def orgunlink(req, uid=None, orgid=None):
    """Remove a user from one or more organizations"""
    # First, sanitize arguments
    if type(orgid) is str:
        orgid = [orgid]
    elif type(orgid) is not list:
        return "Invalid arguments"
    try:
        uid = int(uid)
    except TypeError:
        return "Invalid arguments"

    # Check the the account id is valid
    try:
        account = navprofiles.Account(uid)
        account.load()
    except forgetSQL.NotFound:
        return "No such account id %s" % uid

    # Then, remove the user from each organizations
    successful = []
    for id in orgid:
        link = navprofiles.Accountorg(uid, id)
        try:
            link.load()
            link.delete()
            successful.append(id)
        except forgetSQL.NotFound:
            pass

    if len(successful) > 0:
        req.session['statusMessage'] = "Successfully removed %s from the following organizations: %s" % (
            account.login, ",".join(successful))
    else:
        req.session['statusMessage'] = "%s was not removed from any organizations" % account.login
    web.redirect(req, "account?id=%s" % uid, seeOther=True)
    

def index(req):
    """Default useradmin index page, shows the accountlist."""
    return accountlist(req)
