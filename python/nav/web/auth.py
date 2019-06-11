# Copyright (C) 2010, 2011, 2013, 2019 Uninett AS
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
Contains web authentication and login functionality for NAV,
including NAV authentication and authorization middleware for Django
"""

import logging
import os

from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.sessions.backends.db import SessionStore
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.six.moves.urllib import parse
try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django <= 1.9
    MiddlewareMixin = object

from nav.auditlog.models import LogEntry
from nav.django.utils import is_admin, get_account
from nav.models.profiles import Account, AccountGroup
from nav.web import ldapauth


_logger = logging.getLogger(__name__)


ACCOUNT_ID_VAR = 'account_id'
SUDOER_ID_VAR = 'sudoer'

# This may seem like redundant information, but it seems django's reverse
# will hang under some usages of these middleware classes - so until we figure
# out what's going on, we'll hardcode this here.
LOGIN_URL = '/index/login/'


def _set_account(request, account):
    request.session[ACCOUNT_ID_VAR] = account.id
    request.account = account
    _logger.debug('Set active account to "%s"', account.login)
    request.session.save()


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
        _logger.info("Locked user %s tried to log in", account.login)

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


# Middleware


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _logger.debug(
            'AuthenticationMiddleware < (session: %s, account: %s) from "%s"',
            dict(request.session),
            getattr(request, 'account', 'NOT SET'),
            request.get_full_path(),
        )

        ensure_account(request)
        account = request.account
        session = request.session
        sudo_operator = get_sudoer(request)  # Account or None

        if sudo_operator is not None:
            account.sudo_operator = sudo_operator

        _logger.debug("Request for %s authenticated as user=%s",
                      request.get_full_path(), account.login)
        _logger.debug(
            'AuthenticationMiddleware > (session: %s, account: %s) from "%s"',
            dict(request.session),
            getattr(request, 'account', 'NOT SET'),
            request.get_full_path(),
        )


def ensure_account(request):
    session = request.session

    get_id = getattr(session, ACCOUNT_ID_VAR, Account.DEFAULT_ACCOUNT)
    account = Account.objects.get(id=get_id)

    if account.locked:
        # Switch back to fallback, anonymous user
        account = Account.objects.get(id=Account.DEFAULT_ACCOUNT)

    _set_account(request, account)


class AuthorizationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        account = request.account

        authorized = (authorization_not_required(request.get_full_path())
                      or
                      account.has_perm('web_access', request.get_full_path()))
        if not authorized:
            _logger.warning("User %s denied access to %s",
                            account.login, request.get_full_path())
            return self.redirect_to_login(request)
        else:
            if not account.is_default_account():
                os.environ['REMOTE_USER'] = account.login
            elif 'REMOTE_USER' in os.environ:
                del os.environ['REMOTE_USER']

    def redirect_to_login(self, request):
        """Redirects a request to the NAV login page, unless it was detected
        to be an AJAX request, in which case return a 401 Not Authorized
        response.

        """
        if request.is_ajax():
            return HttpResponse(status=401)

        new_url = '{0}?origin={1}&noaccess'.format(
            LOGIN_URL,
            parse.quote(request.get_full_path()))
        return HttpResponseRedirect(new_url)


def authorization_not_required(fullpath):
    """Checks is authorization is required for the requested url

    Should the user be able to decide this? Currently not.

    """
    auth_not_required = ['/api/', '/doc/']
    for url in auth_not_required:
        if fullpath.startswith(url):
            return True


#
# sudo-related functionality
#


def sudo(request, other_user):
    """Switches the current session to become other_user"""
    if SUDOER_ID_VAR in request.session:
        # Already logged in as another user.
        raise SudoRecursionError()
    if not is_admin(get_account(request)):
        # Check if sudoer is acctually admin
        raise SudoNotAdminError()
    original_user = request.account
    request.session[SUDOER_ID_VAR] = original_user.id
    _set_account(request, other_user)
    _logger.info('Sudo: "%s" acting as "%s"', original_user, other_user)
    LogEntry.add_log_entry(
        original_user,
        'sudo',
        '{actor} sudoed to {target}',
        subsystem='auth',
        target=other_user
    )


def desudo(request):
    """Switches the current session to become the original user from before a
    call to sudo().

    """
    if SUDOER_ID_VAR not in request.session:
        # We are not sudoing
        return

    other_user = request.account
    original_user_id = request.session[SUDOER_ID_VAR]
    original_user = Account.objects.get(id=original_user_id)

    del request.session[ACCOUNT_ID_VAR]
    del request.session[SUDOER_ID_VAR]
    _set_account(request, original_user)
    _logger.info('DeSudo: "%s" no longer acting as "%s"',
                 original_user, request.account)
    LogEntry.add_log_entry(
        original_user,
        'desudo',
        '{actor} no longer sudoed as {target}',
        subsystem='auth',
        target=other_user
    )


def get_sudoer(request):
    """Returns a sudoer's Account, if current session is in sudo-mode"""
    if SUDOER_ID_VAR in request.session:
        return Account.objects.get(id=request.session[SUDOER_ID_VAR])


@python_2_unicode_compatible
class SudoRecursionError(Exception):
    msg = u"Already posing as another user"

    def __str__(self):
        return self.msg


@python_2_unicode_compatible
class SudoNotAdminError(Exception):
    msg = u"Not admin"

    def __str__(self):
        return self.msg


# For testing


def create_session_cookie(username):
    """Creates an active session for username and returns the resulting
    session cookie.

    This is useful to fake login sessions during testing.

    """
    user = Account.objects.get(login=username)
    session = SessionStore()
    session[ACCOUNT_ID_VAR] = user.id
    session.save()

    cookie = {
        'name': settings.SESSION_COOKIE_NAME,
        'value': session.session_key,
        'secure': False,
        'path': '/',
    }
    return cookie
