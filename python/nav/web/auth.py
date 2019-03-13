#
# Copyright (C) 2010, 2011 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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
import logging

from nav.web import ldapauth
from nav.models.profiles import Account

logger = logging.getLogger("nav.web.auth")


def authenticate(username, password):
    """
    Authenticate username and password

    First try LDAP, if available. Then fall back to Account.

    Returns account object if user was authenticated, else None.
    """
    account = authenticate_ldap(username, password)
    if account:
        return account
    if account is False:  # An LDAP user is preferred over a db user
        return None

    account = authenticate_account(username, password)
    if account:
        return account

    # Not authenticated
    return None


def authenticate_ldap(username=None, password=None):
    """
    Authenticate username and password against LDAP, if available

    Returns account object if user was authenticated, False if the user is
    invlid or otherwise is not allowed to log in, else None.
    """
    if not username and not password:
        return None

    if not ldapauth.available:
        return None

    try:
        ldapuser = ldapauth.authenticate(username, password)
    except ldapauth.NoAnswerError:
        # LDAP unreachable, fallback
        return None

    try:
        account = Account.objects.get(login__iexact=username)
    except Account.DoesNotExist:
        # Store the ldapuser in the database and return the new account
        if ldapuser:
            account = Account(
                login=ldapuser.username,
                name=ldapuser.get_real_name(),
                ext_sync='ldap'
            )
            account.set_password(password)
            account.save()
            logger.info("Created user %s from LDAP", account.login)
            return account

    # From this point on we have an existing Account

    if ldapuser is False and account.ext_sync == 'ldap':
        # This account is controlled by LDAP, and LDAP cannot
        # authenticate the user
        logger.warn('Local database is out of sync with LDAP for user {}: '
                    'either the password is wrong or the user is no '
                    'longer registered in LDAP'.format(username))
        return False

    # From this point on we have an authenticated LDAPUser

    # Bail out! Potentially evil user
    if account.locked:
        logger.info("Locked ldap user %s tried to log in", account.login)
        # Needs auditlog
        return False

    # Sync password from ldap to local db
    if not account.check_password(password):
        account.set_password(password)
        logger.info("Synced user %s's password from LDAP", account.login)
        account.save()

    return account


def authenticate_account(username=None, password=None):
    """
    Authenticate username and password against database

    Returns account object if user was authenticated, False if the user is
    invlid or otherwise is not allowed to log in, else None.
    """
    if not username and not password:
        return None

    try:
        account = Account.objects.get(login__iexact=username)
    except Account.DoesNotExist:
        return None

    # Bail out! Potentially evil user
    if account.locked:
        logger.info("Locked user %s tried to log in", account.login)
        # Needs auditlog
        return False

    if account.check_password(password):
        return account

    # Password was incorrect
    return None
