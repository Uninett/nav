"""
$Id$

This file is part of the NAV project.

Contains web authentication functionality for NAV.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
from nav import users
import base64, urllib
import sys, os, re
import nav

from nav import db
from nav.db import navprofiles
from nav.web.preferences import Preferences, Link
from nav.db.navprofiles import Account, Accountnavbar, Navbarlink

def checkAuthorization(user, uri):
    """
    Check whether the given user object is authorized to access the
    specified URI)
    """
    # First make sure we are connected to the navprofile database.
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
    web.redirect(req, '/index.py/login?origin=%s' % urllib.quote(req.unparsed_uri), temporary=True)

def _find_user_preferences(user, req):
    if not hasattr(user, "preferences"):
        # if user preferences is not loaded, it's time to do so
        user.preferences = Preferences()
        conn = nav.db.getConnection('navprofile', 'navprofile')
        nav.db.navprofiles.setCursorMethod(conn.cursor)
        prefs = user.getChildren(Accountnavbar)
        if not prefs:
            # if user has no preferences set, use default preferences
            default = Account(0)
            prefs = default.getChildren(Accountnavbar)
        for pref in prefs:
            link = Navbarlink(pref.navbarlink)
            if pref.positions.count('navbar'): # does 'positions'-string contain 'navbar'
                user.preferences.navbar.append(Link(link.name, link.uri))
            if pref.positions.count('qlink1'): # does 'positions'-string contain 'qlink1'
                user.preferences.qlink1.append(Link(link.name, link.uri))
            if pref.positions.count('qlink2'): # does 'positions'-string contain 'qlink2'
                user.preferences.qlink2.append(Link(link.name, link.uri))
        req.session.save() # remember this to next time

def authenticate(req):
    """
    Authenticate and authorize the client that sent this request.  If
    the authenticated (or unauthenticated) user is found to be not
    authorized to request this URI, we redirect him/her to the login
    page.
    """
    if not req.session.has_key('user'):
        # If no Account object is registered with this session, we
        # load and register the default Account (which is almost a
        # synonym for Anonymous user)
        conn = db.getConnection('navprofile', 'navprofile')
        cursor = conn.cursor()
        navprofiles.setCursorMethod(conn.cursor)
        req.session['user'] = Account(0)

    user = req.session['user']
    _find_user_preferences(user, req)
    
    if not checkAuthorization(user, req.unparsed_uri):
        redirectToLogin(req)
    else:
        if not user.id == 0:
            os.environ['REMOTE_USER'] = user.login
        elif os.environ.has_key('REMOTE_USER'):
            del os.environ['REMOTE_USER']
        return True

# For fun, we give the authenticate function an alternative name.
authorize = authenticate
