# Copyright (C) 2010, 2011, 2013, 2019 Uninett AS
# Copyright (C) 2022 Sikt
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
Contains web authentication and login functionality for NAV.

The "*Middleware" is Django-specific.
"""

from datetime import datetime
import logging
from os.path import join
import os

from urllib import parse

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django <= 1.9
    MiddlewareMixin = object

try:
    # Python 3.6+
    import secrets

    def fake_password(length):
        return secrets.token_urlsafe(length)

except ImportError:
    from random import choice
    import string

    def fake_password(length):
        symbols = string.ascii_letters + string.punctuation + string.digits
        return u"".join(choice(symbols) for i in range(length))


from nav.auditlog.models import LogEntry
from nav.config import NAVConfigParser
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
# The local logout url, redirects to '/' after logout
# If the entire site is protected via remote_user, this link must be outside
# that protection!
LOGOUT_URL = '/index/logout/'


class RemoteUserConfigParser(NAVConfigParser):
    DEFAULT_CONFIG_FILES = [join('webfront', 'webfront.conf')]
    DEFAULT_CONFIG = u"""
[remote-user]
enabled=no
login-url=
logout-url=
varname=REMOTE_USER
workaround=none
"""


_config = RemoteUserConfigParser()


def _set_account(request, account):
    request.session[ACCOUNT_ID_VAR] = account.id
    request.account = account
    _logger.debug('Set active account to "%s"', account.login)
    request.session.save()


def authenticate(username, password):
    """Authenticate username and password against database.
    Returns account object if user was authenticated, else None.
    """
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
                    login=user.username, name=user.get_real_name(), ext_sync='ldap'
                )
                account.set_password(password)
                account.save()
                _handle_ldap_admin_status(user, account)
                # We're authenticated now
                auth = True

    if account and account.locked:
        _logger.info("Locked user %s tried to log in", account.login)

    if (
        account
        and account.ext_sync == 'ldap'
        and ldapauth.available
        and not auth
        and not account.locked
    ):
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
            nav_account.groups.add(admin_group)
        else:
            nav_account.groups.remove(admin_group)


def authenticate_remote_user(request):
    """Authenticate username from http header REMOTE_USER

    Returns:

    :return: If the user was authenticated, an account.
             If the user was blocked from logging in, False.
             Otherwise, None.
    :rtype: Account, False, None
    """
    username = get_remote_username(request)
    if not username:
        return None

    # We now have a username-ish

    try:
        account = Account.objects.get(login=username)
    except Account.DoesNotExist:
        # Store the remote user in the database and return the new account
        account = Account(login=username, name=username, ext_sync='REMOTE_USER')
        account.set_password(fake_password(32))
        account.save()
        _logger.info("Created user %s from header REMOTE_USER", account.login)
        template = 'Account "{actor}" created due to REMOTE_USER HTTP header'
        LogEntry.add_log_entry(
            account, 'create-account', template=template, subsystem='auth'
        )
        return account

    # Bail out! Potentially evil user
    if account.locked:
        _logger.info("Locked user %s tried to log in", account.login)
        template = 'Account "{actor}" was prevented from logging in: blocked'
        LogEntry.add_log_entry(
            account, 'login-prevent', template=template, subsystem='auth'
        )
        return False

    return account


def get_login_url(request):
    """Calculate which login_url to use"""
    path = parse.quote(request.get_full_path())
    if path == "/":
        default_new_url = LOGIN_URL
    else:
        default_new_url = '{0}?origin={1}&noaccess'.format(LOGIN_URL, path)
    remote_loginurl = get_remote_loginurl(request)
    return remote_loginurl if remote_loginurl else default_new_url


def get_logout_url(request):
    """Calculate which logout_url to use"""
    remote_logouturl = get_remote_logouturl(request)
    if remote_logouturl and remote_logouturl.endswith('='):
        remote_logouturl += request.build_absolute_uri(LOGOUT_URL)
    return remote_logouturl if remote_logouturl else LOGOUT_URL


def get_remote_loginurl(request):
    """Return a url (if set) to log in to/via a remote service

    :return: Either a string with an url, or None.
    :rtype: str, None
    """
    return get_remote_url(request, 'login-url')


def get_remote_logouturl(request):
    """Return a url (if set) to log out to/via a remote service

    :return: Either a string with an url, or None.
    :rtype: str, None
    """
    return get_remote_url(request, 'logout-url')


def get_remote_url(request, urltype):
    """Return a url (if set) to a remote service for REMOTE_USER purposes

    :return: Either a string with an url, or None.
    :rtype: str, None
    """
    remote_url = None
    try:
        if not _config.getboolean('remote-user', 'enabled'):
            return None
        remote_url = _config.get('remote-user', urltype)
    except ValueError:
        return None
    if remote_url:
        nexthop = request.build_absolute_uri(request.get_full_path())
        remote_url = remote_url.format(nexthop)
    return remote_url


def get_remote_username(request):
    """Return the username in REMOTE_USER if set and enabled

    :return: The username in REMOTE_USER if any, or None.
    :rtype: str, None
    """
    try:
        if not _config.getboolean('remote-user', 'enabled'):
            return None
    except ValueError:
        return None

    if not request:
        return None

    workaround = 'none'
    try:
        workaround_config = _config.get('remote-user', 'workaround')
    except ValueError:
        pass
    else:
        if workaround_config in REMOTE_USER_WORKAROUNDS:
            workaround = workaround_config

    username = REMOTE_USER_WORKAROUNDS[workaround](request)

    if not username:
        return None

    return username


def _get_remote_user_varname():
    varname = 'REMOTE_USER'
    try:
        varname = _config.get('remote-user', 'varname')
    except ValueError:
        pass
    return varname


def _workaround_default(request):
    varname = _get_remote_user_varname()
    username = request.META.get(varname, '').strip()
    return username


def _workaround_feide_oidc(request):
    varname = _get_remote_user_varname()
    username = request.META.get(varname, '').strip()
    if ':' in username:
        username = username.split(':', 1)[1]
    return username


REMOTE_USER_WORKAROUNDS = {
    'none': _workaround_default,
    'feide-oidc': _workaround_feide_oidc,
}


# Middleware


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _logger.debug(
            'AuthenticationMiddleware ENTER (session: %s, account: %s) from "%s"',
            dict(request.session),
            getattr(request, 'account', 'NOT SET'),
            request.get_full_path(),
        )
        ensure_account(request)

        account = request.account
        sudo_operator = get_sudoer(request)  # Account or None
        logged_in = sudo_operator or account
        _logger.debug(
            ('AuthenticationMiddleware ' '(logged_in: "%s" acting as "%s") from "%s"'),
            logged_in.login,
            account.login,
            request.get_full_path(),
        )

        remote_username = get_remote_username(request)
        if remote_username:
            _logger.debug(
                ('AuthenticationMiddleware: ' '(REMOTE_USER: "%s") from "%s"'),
                remote_username,
                request.get_full_path(),
            )
            if logged_in.id == Account.DEFAULT_ACCOUNT:
                # Switch from anonymous to REMOTE_USER
                login_remote_user(request)
            elif remote_username != logged_in.login:
                # REMOTE_USER has changed, logout
                logout(request, sudo=bool(sudo_operator))
                sudo_operator = None
                # Activate anonymous account for AuthorizationMiddleware's sake
                ensure_account(request)

        if sudo_operator is not None:
            request.account.sudo_operator = sudo_operator

        _logger.debug(
            'AuthenticationMiddleware EXIT (session: %s, account: %s) from "%s"',
            dict(request.session),
            getattr(request, 'account', 'NOT SET'),
            request.get_full_path(),
        )


def ensure_account(request):
    """Guarantee that valid request.account is set"""
    session = request.session

    if not ACCOUNT_ID_VAR in session:
        session[ACCOUNT_ID_VAR] = Account.DEFAULT_ACCOUNT

    account = Account.objects.get(id=session[ACCOUNT_ID_VAR])

    if account.locked:
        # Switch back to fallback, the anonymous user
        # Assumes nobody has locked it..
        account = Account.objects.get(id=Account.DEFAULT_ACCOUNT)

    _set_account(request, account)


def login_remote_user(request):
    """Log in the user in REMOTE_USER, if any and enabled

    :return: Account for remote user, or None
    :rtype: Account, None
    """
    remote_username = get_remote_username(request)
    if remote_username:
        # Get or create an account from the REMOTE_USER http header
        account = authenticate_remote_user(request)
        if account:
            request.session[ACCOUNT_ID_VAR] = account.id
            request.account = account
            return account
    return None


class AuthorizationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        account = request.account

        authorized = authorization_not_required(
            request.get_full_path()
        ) or account.has_perm('web_access', request.get_full_path())
        if not authorized:
            _logger.warning(
                "User %s denied access to %s", account.login, request.get_full_path()
            )
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

        new_url = get_login_url(request)
        return HttpResponseRedirect(new_url)


def authorization_not_required(fullpath):
    """Checks is authorization is required for the requested url

    Should the user be able to decide this? Currently not.

    """
    auth_not_required = [
        '/api/',
        '/doc/',  # No auth/different auth system
        '/about/',
        '/index/login/',
        '/refresh_session',
    ]
    for url in auth_not_required:
        if fullpath.startswith(url):
            _logger.debug('authorization_not_required: %s', url)
            return True


def logout(request, sudo=False):
    """Log out a user from a request

    Returns a safe, public path useful for callers building a redirect."""
    # Ensure that logout can safely be called whenever
    if not (hasattr(request, 'session') and hasattr(request, 'account')):
        _logger.debug('logout: not logged in')
        return None
    if sudo or request.method == 'POST' and 'submit_desudo' in request.POST:
        desudo(request)
        return reverse('webfront-index')
    else:
        account = request.account
        del request.session[ACCOUNT_ID_VAR]
        del request.account
        request.session.set_expiry(datetime.now())
        request.session.save()
        _logger.debug('logout: logout %s', account.login)
        LogEntry.add_log_entry(account, 'log-out', '{actor} logged out', before=account)
    _logger.debug('logout: redirect to "/" after logout')
    return u'/'


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
    _logger.debug(
        'Sudo: (session: %s, account: %s)', dict(request.session), request.account
    )
    LogEntry.add_log_entry(
        original_user,
        'sudo',
        '{actor} sudoed to {target}',
        subsystem='auth',
        target=other_user,
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
    _logger.info(
        'DeSudo: "%s" no longer acting as "%s"', original_user, request.account
    )
    _logger.debug(
        'DeSudo: (session: %s, account: %s)', dict(request.session), request.account
    )
    LogEntry.add_log_entry(
        original_user,
        'desudo',
        '{actor} no longer sudoed as {target}',
        subsystem='auth',
        target=other_user,
    )


def get_sudoer(request):
    """Returns a sudoer's Account, if current session is in sudo-mode"""
    if SUDOER_ID_VAR in request.session:
        return Account.objects.get(id=request.session[SUDOER_ID_VAR])


class SudoRecursionError(Exception):
    msg = u"Already posing as another user"

    def __str__(self):
        return self.msg


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
