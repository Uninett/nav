"""
$Id$

This file is part of the NAV project.

Contains web authentication functionality for NAV.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
from nav import users
import base64
import re
import sys
import os

ADMINGROUP = 1
ANONYMOUSGROUP = 2

def checkAuthorization(user, uri):
    """Check whether the given user object is authorized to access the
    specified URI)"""

    from nav import db
    from nav.db import navprofiles
    conn = db.getConnection('navprofile', 'navprofile')
    cursor = conn.cursor()
    navprofiles.setCursorMethod(conn.cursor)

    if user:
        groups = user.getGroups()
    else:
        groups = []

    # If the user is a member of the administrator group, he is
    # _always_ granted access to _everything_.
    if ADMINGROUP in [group.id for group in groups]:
        return True

    # If the user is not a registered member of the anonymous group,
    # we still assume he is - because ALL users have at least the
    # privileges of anonymous users.
    if not ANONYMOUSGROUP in [group.id for group in groups]:
        from nav.db.navprofiles import Accountgroup
        groups.append(Accountgroup(ANONYMOUSGROUP))

    if len(groups):  # If any groups were found
        groupString = ",".join([str(group.id) for group in groups])
        cursor.execute("SELECT * FROM WebAuthorization WHERE accountgroupid IN (%s)" % groupString)
        for authz in cursor.dictfetchall():
            regex = re.compile(authz['uri'])
            if regex.search(uri):
                return True

    # If no groups or uri matches were found, we return false.
    return False
    

def redirectToLogin(req):
    """
    Takes the supplied request and redirects it to the NAV login page.
    """
    from nav import web
    web.redirect(req, '/index.py/login?origin=%s' % req.uri, temporary=True)

def authenticate(req):
    """
    Authenticate and authorize the client that sent this request.  If
    the authenticated (or unauthenticated) user is found to be not
    authorized to request this URI, we redirect him/her to the login
    page.
    """
    if req.session and req.session.has_key('user'):
        user = req.session['user']
    else:
        user = None
        
    if not checkAuthorization(user, req.uri):
        redirectToLogin(req)
    else:
        if user:
            os.environ['REMOTE_USER'] = user.login
        elif os.environ.has_key('REMOTE_USER'):
            del os.environ['REMOTE_USER']
        return True

# For fun, we give the authenticate function an alternative name.
authorize = authenticate
