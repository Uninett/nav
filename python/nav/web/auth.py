#
# Copyright (C) 2010, 2011, 2019 Uninett AS
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
from nav.models.profiles import Account, AccountGroup

logger = logging.getLogger("nav.web.auth")


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
                _handle_ldap_admin_status(user, account)
                # We're authenticated now
                auth = True

    if account and account.locked:
        logger.info("Locked user %s tried to log in", account.login)

    if (account and
            account.ext_sync == 'ldap' and
            ldapauth.available and
            not auth and
            not account.locked):
        try:
            auth = ldapauth.authenticate(username, password)
        except ldapauth.NoAnswerError:
            # Fallback to stored password if ldap is unavailable
            auth = False
        else:
            if auth:
                account.set_password(password)
                account.save()
                _handle_ldap_admin_status(auth, account)
            else:
                return

    if account and not auth:
        auth = account.check_password(password)

    if auth and account:
        return account
    else:
        return None


def _handle_ldap_admin_status(ldap_user, nav_account):
    is_admin = ldap_user.is_admin()
    # Only modify admin status if an entitlement is configured in webfront.conf
    if is_admin is not None:
        admin_group = AccountGroup.objects.get(id=AccountGroup.ADMIN_GROUP)
        if is_admin:
            nav_account.accountgroup_set.add(admin_group)
        else:
            nav_account.accountgroup_set.remove(admin_group)
