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

from nav.web import state, ldapAuth
from nav.models.profiles import Account, AccountNavbar, NavbarLink

logger = logging.getLogger("nav.web.auth")

def redirectToLogin(req):
    """
    Takes the supplied request and redirects it to the NAV login page.
    """
    from nav import web
    web.redirect(req, '/index/login?origin=%s' % urllib.quote(req.unparsed_uri), temporary=True)

# FIXME Should probably be refactored out if this file, as it does not directly
# have anything to do with authentication.
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

def authorize(req):
    '''Authorize the request from the user.
    Returns True if the user was authorized, else False.
    '''
    if not req.session.has_key('user'):
        # If no Account object is registered with this session, we
        # load and register the default Account (which is almost a
        # synonym for Anonymous user)
        account = Account.objects.get(id=Account.DEFAULT_ACCOUNT)
        req.session['user'] = {
            'id': account.id,
            'login': account.login,
            'name': account.name,
        }
    else:
        account = Account.objects.get(id=req.session['user']['id'])

    user = req.session['user']
    logger.debug("Request for %s authenticated as user=%s", req.unparsed_uri,
                 user['login'])
    _find_user_preferences(user, req)

    # Now we can check if the user is authorized for this request.
    authorized = account.has_perm('web_access', req.unparsed_uri)
    if not authorized:
        logger.warn("User %s denied access to %s", user['login'],
                    req.unparsed_uri)
        return False
    else:
        if not user['id'] == 0:
            os.environ['REMOTE_USER'] = user['login']
        elif os.environ.has_key('REMOTE_USER'):
            del os.environ['REMOTE_USER']
        return True

def authenticate(username, password):
    '''Authenticate username and password against database.
    Returns account object if user was authenticated, else None.
    '''
    # FIXME Log stuff?
    auth = False
    account = None

    # Try to find the account in the database. If it's not found we can try
    # LDAP.
    try:
        account = Account.objects.get(login=username)
    except Account.DoesNotExist:
        if ldapAuth.available:
            auth = ldapAuth.authenticate(username, password)
            # If we authenticated, store the user in database.
            if auth:
                name = ldapAuth.getUserName(username)
                account = Account(
                    login=username,
                    name=name,
                    ext_sync='ldap'
                )
                account.set_password(password)
                account.save()

    if account and not auth:
        if account.ext_sync == 'ldap' and ldapAuth.available:
            # Try to authenticate with LDAP if user has specified this.
            auth = ldapAuth.authenticate(username, password)
            if auth:
                account.set_password(password)
                account.save()
        else:
            # Authenticate against database
            auth = account.check_password(password)

    if auth and account:
        return account
    else:
        return None

def login(request, account):
    '''Set user as authenticated in the session object.
    Will fail if user is not authenticated first.
    '''
    # Invalidate old sessions
    if request.session.has_key('user'):
        del request.session['user']
        request.session.save()

    request.session['user'] = {
        'id': account.id,
        'login': account.login,
        'name': account.name,
    }
    request.session.save()

def logout(request):
    '''Removes session object for this user.
    In effect, this is the same as logging out.
    '''
    # The session is stored in the mod_python request. This little if makes it
    # possible to pass both django and mod_python requests.
    if isinstance(request, ModPythonRequest):
        request = request._req
    del request.session
    state.deleteSessionCookie(request)

def sudo(request, other_user):
    if hasattr(request, '_req'):
        request = request._req

    current_user = request.session['user']
    request.session['user'] = {
        'id': other_user.id,
        'login': other_user.login,
        'name': other_user.name,
        'sudoer': current_user,
    }
    request.session.save()

def desudo(request):
    if hasattr(request, '_req'):
        request = request._req

    current_user = request.session['user']
    if current_user.has_key('sudoer'):
        original_user = current_user['sudoer']

    del request.session['user']
    request.session.save()
    request.session['user'] = {
        'id': original_user['id'],
        'login': original_user['login'],
        'name': original_user['name'],
    }
    request.session.save()
