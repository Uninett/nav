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

def checkAuthorization(user, uri):
    """Check whether the given user object is authorized to access the
    specified URI)"""

    from nav import db
    from nav.db import navprofiles
    conn = db.getConnection('navprofile', 'navprofile')
    cursor = conn.cursor()
    navprofiles.setCursorMethod(conn.cursor)
    anonGroup = 2

    if user:
        groups = user.getGroups()
    else:
        from nav.db.navprofiles import Accountgroup
        groups = [Accountgroup(2)]

    groupString = ",".join([str(group.id) for group in groups])
    cursor.execute("SELECT * FROM WebAuthorization WHERE accountgroupid IN (%s)" % groupString)
    for authz in cursor.dictfetchall():
        regex = re.compile(authz['uri'])
        if regex.search(uri):
            return True

    # If none matched, we return false.
    return False
    

def redirectToLogin(req):
    """
    Takes the supplied request and redirects it to the NAV login page.
    """
    from mod_python import apache
    req.headers_out['Location'] = '/index.py/login?origin=%s' % req.uri
    req.status = apache.HTTP_TEMPORARY_REDIRECT
    req.send_http_header()
    raise apache.SERVER_RETURN, apache.HTTP_TEMPORARY_REDIRECT

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
        return True

# For fun, we give the authenticate function an alternative name.
authorize = authenticate
