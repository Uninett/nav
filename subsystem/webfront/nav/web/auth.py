# -*- coding: utf-8 -*-
#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Contains web authentication functionality for NAV.
"""
import base64, urllib
import sys, os, re
import nav
import logging

from nav.models.profiles import Account, AccountNavbar, NavbarLink

logger = logging.getLogger("nav.web.auth")

def checkAuthorization(user, uri):
    """
    Check whether the given user object is authorized to access the
    specified URI)
    """
    # First make sure we are connected to the navprofile database.
#    conn = db.getConnection('navprofile', 'navprofile')
#    cursor = conn.cursor()

    # When the connection has been made, we make use of the privilege
    # system to discover whether the user has access to this uri or
    # not.
    return Account.objects.get(id=user['id']).has_perm('web_access', uri)

def redirectToLogin(req):
    """
    Takes the supplied request and redirects it to the NAV login page.
    """
    from nav import web
    web.redirect(req, '/index/login?origin=%s' % urllib.quote(req.unparsed_uri), temporary=True)

def _find_user_preferences(user, req):
    if not hasattr(user, "preferences"):
        # if user preferences is not loaded, it's time to do so
        user['preferences'] = {
            'navbar': [],
            'qlink1': [],
            'qlink2': [],
            'hidelogo': 0,
        }
        prefs = AccountNavbar.objects.select_related(
            'navbarlink'
        ).filter(account__id=user['id'])

        if prefs.count() == 0:
            # if user has no preferences set, use default preferences
            prefs = AccountNavbar.objects.select_related(
                'navbarlink'
            ).filter(account__id=0)

        for pref in prefs:
            link = {
                'name': pref.navbarlink.name,
                'uri': pref.navbarlink.uri,
            }
            if pref.positions.count('navbar'): # does 'positions'-string contain 'navbar'
                user['preferences']['navbar'].append(link)
            if pref.positions.count('qlink1'): # does 'positions'-string contain 'qlink1'
                user['preferences']['qlink1'].append(link)
            if pref.positions.count('qlink2'): # does 'positions'-string contain 'qlink2'
                user['preferences']['qlink2'].append(link)
        if req:
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
        #conn = db.getConnection('navprofile', 'navprofile')
        #cursor = conn.cursor()

        # FIXME Should we load, or just make a new account object?
        account = Account.objects.get(id=0)
        req.session['user'] = {
            'id': account.id,
            'login': account.login,
            'name': account.name,
        }

    user = req.session['user']
    logger.debug("Request for %s authenticated as user=%s", req.unparsed_uri,
                 user['login'])
    _find_user_preferences(user, req)

    if not checkAuthorization(user, req.unparsed_uri):
        logger.warn("User %s denied access to %s", user['login'],
                    req.unparsed_uri)
        redirectToLogin(req)
    else:
        if not user['id'] == 0:
            os.environ['REMOTE_USER'] = user['login']
        elif os.environ.has_key('REMOTE_USER'):
            del os.environ['REMOTE_USER']
        return True

# For fun, we give the authenticate function an alternative name.
authorize = authenticate
