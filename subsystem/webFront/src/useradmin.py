"""
$Id$

This file is part of the NAV project.

This module represents the useradmin pages of the NAV web interface.
It follows the mod_python.publisher paradigm.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
#from mod_python import apache
import os, nav, psycopg
from nav import web, db
from nav.db import navprofiles
from nav.web.templates.useradmin import *

# Make sure the database connection is always there
_profileConn = db.getConnection('navprofile', 'navprofile')
navprofiles.setCursorMethod(_profileConn.cursor)
_profileCursor = _profileConn.cursor
_manageConn = db.getConnection('webfront', 'manage')
_manageCursor = _manageConn.cursor

def _getAccounts(includeIds=[], excludeIds=[], forGroup=None):
    """Return a list of rows from the Account table"""
    criteria = []
    if len(includeIds) > 0:
        criteria.append("a.id IN (%s)" % ','.join([str(x) for x in includeIds]))
    if len(excludeIds) > 0:
        criteria.append("a.id NOT IN (%s)" % ','.join([str(x) for x in excludeIds]))
    if forGroup is not None:
        criteria.append("b.groupid=%d" % forGroup)

    if len(criteria) > 0:
        whereClause = "WHERE %s" % " AND ".join(criteria)
    else:
        whereClause = ""
    
    cursor = _profileCursor()
    sql = \
        """SELECT a.id, a.login, a.name, a.ext_sync, COUNT(b.groupid) AS groupcount
        FROM account AS a
        LEFT JOIN accountingroup AS b
        ON a.id = b.accountid
        %s
        GROUP BY a.id, a.login, a.name, a.ext_sync
        ORDER BY a.login""" % whereClause
    cursor.execute(sql)
    return cursor.dictfetchall()

def _getGroups(includeIds=[], excludeIds=[], forAccount=None):
    """Return a list of rows from the AccountGroup table"""
    criteria = []
    if len(includeIds) > 0:
        criteria.append("g.id IN (%s)" % ','.join([str(x) for x in includeIds]))
    if len(excludeIds) > 0:
        criteria.append("g.id NOT IN (%s)" % ','.join([str(x) for x in excludeIds]))
    if forAccount is not None:
        criteria.append("b.accountid=%d" % forAccount)

    if len(criteria) > 0:
        whereClause = "WHERE %s" % " AND ".join(criteria)
    else:
        whereClause = ""
    
    cursor = _profileCursor()
    sql = \
        """SELECT g.id, g.name, g.descr AS description, COUNT(b.accountid) AS membercount
        FROM accountgroup AS g
        LEFT JOIN accountingroup AS b
        ON g.id = b.groupid
        %s
        GROUP BY g.id, g.name, g.descr
        ORDER BY g.name""" % whereClause
    cursor.execute(sql)
    return cursor.dictfetchall()

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
    return page

def grouplist(req):
    """Display a list of the groups registered within NAV."""
    page = GroupList()
    page.groups = _getGroups()
    page.path[-1] = ("Group list", False)
    return page

def account(req, id=None):
    """Display all relevant data about an Account in an editable form."""
    page = AccountPage()
    page.path[-1] = ("Edit account", False)
    if id is not None:
        # Sanitary work on arguments
        try:
            id = int(id)
        except:
            return "%s is not a valid account id" % repr(id)

        accounts = _getAccounts(includeIds=[id])
        if len(accounts) < 1:
            return "no such account %s" % id
        else:
            account = accounts[0]

        page.newAccount = False
        page.information = "Editing account \"%s\" (#%s)" % (account['name'], account['id'])
        page.account = account
        page.editable = account['ext_sync'] is None or account['ext_sync'] == ''
        page.account['groups'] = _getGroups(forAccount=id)
    else:
        page.newAccount = True
        page.information = "Creating new user"
        page.account = {'id': None,
                        'login': '',
                        'name': 'New user',
                        'ext_sync': None,
                        'groups': []}
        page.editable = True
        
    page.title = page.information
    # We've filled out most of the details of the account and its
    # group memberships, now we need to fill out the list of groups it
    # has no membership to so that we may add the account to any of
    # these
    groupIds = [ group['id'] for group in page.account['groups'] ]
    page.account['nongroups'] = _getGroups(excludeIds=groupIds)

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
        except:
            return "%s is not a valid group id" % repr(id)

        groups = _getGroups(includeIds=[id])
        if len(groups) < 1:
            return "no such group %s" % id
        else:
            group = groups[0]

        page.newGroup = False
        page.information = "Editing group \"%s\" (#%s)" % (group['name'], group['id'])
        page.group = group
        page.editable = True
        page.group['members'] = _getAccounts(forGroup=id)
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
    # We've filled out most of the details of the group and its
    # members, now we need to fill out the list of non-members so that
    # we may add new members to this group on this form.
    memberIds = [ member['id'] for member in page.group['members'] ]
    page.group['nonmembers'] = _getAccounts(excludeIds=memberIds)

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
    groupStruct = {'id': id,
                   'name': name,
                   'description': description}

    if id is not None:
        redir = 'group?id=%s' % id
    else:
        redir = 'group'

    if _storeGroup(groupStruct):
        req.session['statusMessage'] = "Data saved"
    else:
        req.session['statusMessage'] = "Failed to store the data"

    web.redirect(req, redir, seeOther=True)

def accountsubmit(req, id=None, login=None, name=None, password='', passwordConfirm=''):
    """Receives and stores information submitted from the account
    form."""
    accountStruct = {'id': id,
                     'login': login,
                     'name': name,
                     'password': password}

    if id is not None:
        redir = 'account?id=%s' % id
    else:
        redir = 'account'

    if password != passwordConfirm:
        req.session['statusMessage'] = "Passwords do not match"
    elif _storeAccount(accountStruct):
        req.session['statusMessage'] = "Data saved"
    else:
        req.session['statusMessage'] = "Failed to store the data"

    web.redirect(req, redir, seeOther=True)

def index(req):
    """Default useradmin index page, shows the accountlist."""
    return accountlist(req)

