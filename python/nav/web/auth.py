#
# Copyright (C) 2003, 2004 Norwegian University of Science and Technology
# Copyright (C) 2010, 2011 UNINETT AS
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
import urllib
import os
import logging

from nav.web import ldapauth
from nav.models.profiles import Account, AccountNavbar

logger = logging.getLogger("nav.web.auth")

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
            if pref.positions.count('navbar'):
                user['preferences']['navbar'].append(link)
            if pref.positions.count('qlink1'):
                user['preferences']['qlink1'].append(link)
            if pref.positions.count('qlink2'):
                user['preferences']['qlink2'].append(link)
        if req:
            req.session.save() # remember this to next time


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
        account = Account.objects.get(login__iexact=username)
    except Account.DoesNotExist:
        if ldapauth.available:
            user = ldapauth.authenticate(username, password)
            # If we authenticated, store the user in database.
            if user:
                account = Account(
                    login=user.username,
                    name=user.get_real_name(),
                    ext_sync='ldap'
                )
                account.set_password(password)
                account.save()
                # We're authenticated now
                auth = True

    if (account and account.ext_sync == 'ldap' and
        ldapauth.available and not auth):
        try:
            auth = ldapauth.authenticate(username, password)
        except ldapauth.NoAnswerError:
            # Fallback to stored password if ldap is unavailable
            auth = False
        else:
            if auth:
                account.set_password(password)
                account.save()
            else:
                return

    if account and not auth:
        auth = account.check_password(password)

    if auth and account:
        return account
    else:
        return None
