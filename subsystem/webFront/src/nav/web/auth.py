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
import nav

def checkAuthorization(user, uri):
    """
    Check whether the given user object is authorized to access the
    specified URI)
    """
    # First make sure we are connected to the navprofile database.
    from nav import db
    from nav.db import navprofiles
    conn = db.getConnection('navprofile', 'navprofile')
    cursor = conn.cursor()
    navprofiles.setCursorMethod(conn.cursor)

    # When the connection has been made, we make use of the privilege
    # system to discover whether the user has access to this uri or
    # not.
    return nav.auth.hasPrivilege(user, 'web_access', uri)

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
