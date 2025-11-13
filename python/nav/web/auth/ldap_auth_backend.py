#
# Copyright (C) 2025 Sikt
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
LDAP authentication backend for Django's authentication framework, supporting the
specific legacy quirks of LDAP authentication in NAV.
"""

import logging
from typing import TYPE_CHECKING, Optional

from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from nav.models.profiles import Account, AccountGroup
from nav.web.auth import ldap

if TYPE_CHECKING:
    from nav.web.auth.ldap import LDAPUser


_logger = logging.getLogger(__name__)


class LdapBackend(ModelBackend):
    """
    Authenticates against NAV's LDAP module.

    This backend needs to be listed before `django.contrib.auth.backends.ModelBackend`
    in the `AUTHENTICATION_BACKENDS` setting in order for LDAP-based login flow to
    function correctly.

    Part of the workflow is to hash and store the last know good LDAP password in the
    local NAV account.  If the LDAP server becomes unresponsive, the authentication
    flow will fall back to allowing a returning user to login using their last know good
    password.  A potential weakness of this approach is that disabled/removed users
    may be able to log in to NAV during an LDAP outage if the NAV admin has not
    explicitly removed their local NAV accounts.
    """

    def authenticate(
        self,
        request: Optional[HttpRequest] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ) -> Optional[Account]:
        if not ldap.available:
            return None
        if username is None or password is None:
            return None

        if nav_user := Account.objects.filter(login=username).first():
            if not self._is_an_ldap_synced_user(nav_user):
                return None

        if not (ldap_user := self._ldap_authenticate(username, password)):
            # If we got here without PermissionDenied being raised, then LDAP did
            # not respond, so we fall back to other backends
            return None

        if not nav_user:
            nav_user = self._create_nav_account(ldap_user, password)
        elif not nav_user.is_active:
            # Don't let deactivated users log in
            raise PermissionDenied

        self._sync_nav_account(ldap_user, nav_user, password)
        return nav_user

    @staticmethod
    def _is_an_ldap_synced_user(nav_user: Account) -> bool:
        """Determines whether the given NAV account is an LDAP-synced user."""
        return nav_user.ext_sync == 'ldap'

    @staticmethod
    def _ldap_authenticate(username: str, password: str) -> Optional["LDAPUser"]:
        """Attempts to authenticate the user against LDAP, logging errors"""
        try:
            ldap_user = ldap.authenticate(username, password)
        except ldap.NoAnswerError:
            # There is no way to communicate to the user that the LDAP server isn't
            # responding in the case where this is the user's first login to NAV.
            # XXX: Maybe find a way to add this somehow?
            _logger.error("LDAP server not responding, falling back to local auth")
            return None
        else:
            if not ldap_user:
                raise PermissionDenied
            return ldap_user

    @staticmethod
    def _create_nav_account(ldap_user: "LDAPUser", password: str) -> Account:
        """Creates a new local NAV account based on LDAP user details."""
        nav_account = Account(
            login=ldap_user.username, name=ldap_user.get_real_name(), ext_sync='ldap'
        )
        # We need to set a password right away to ensure the account is considered
        # active before the login process moves on:
        nav_account.set_password(password)
        nav_account.save()
        return nav_account

    @classmethod
    def _sync_nav_account(
        cls, ldap_user: "LDAPUser", nav_user: Account, password: str
    ) -> None:
        """Ensures the necessary local account details are synced from LDAP user
        details.
        """
        nav_user.set_password(password)
        nav_user.save()
        cls._sync_nav_account_admin_privileges_from_ldap(ldap_user, nav_user)

    @staticmethod
    def _sync_nav_account_admin_privileges_from_ldap(
        ldap_user: "LDAPUser", nav_account: Account
    ) -> None:
        """Synchronizes the admin privileges of a given NAV account based on LDAP
        configuration parameters and the LDAP user object entitlements.
        """
        is_admin = ldap_user.is_admin()
        # Only modify admin status if an entitlement is configured in webfront.conf
        if is_admin is not None:
            admin_group = AccountGroup.objects.get(id=AccountGroup.ADMIN_GROUP)
            if is_admin:
                nav_account.groups.add(admin_group)
            else:
                nav_account.groups.remove(admin_group)
