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

from urllib import parse

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django <= 1.9
    MiddlewareMixin = object


from nav.auditlog.models import LogEntry
from nav.models.profiles import Account, AccountGroup
from nav.web.auth import ldap, remote_user
from nav.web.auth.sudo import desudo, get_sudoer
from nav.web.auth.utils import _set_account, ACCOUNT_ID_VAR


_logger = logging.getLogger(__name__)


# This may seem like redundant information, but it seems django's reverse
# will hang under some usages of these middleware classes - so until we figure
# out what's going on, we'll hardcode this here.
LOGIN_URL = '/index/login/'
# The local logout url, redirects to '/' after logout
# If the entire site is protected via remote_user, this link must be outside
# that protection!
LOGOUT_URL = '/index/logout/'


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
        if ldap.available:
            user = ldap.authenticate(username, password)
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
        and ldap.available
        and not auth
        and not account.locked
    ):
        try:
            auth = ldap.authenticate(username, password)
        except ldap.NoAnswerError:
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


def get_login_url(request):
    """Calculate which login_url to use"""
    path = parse.quote(request.get_full_path())
    if path == "/":
        default_new_url = LOGIN_URL
    else:
        default_new_url = '{0}?origin={1}&noaccess'.format(LOGIN_URL, path)
    remote_loginurl = remote_user.get_loginurl(request)
    return remote_loginurl if remote_loginurl else default_new_url


def get_logout_url(request):
    """Calculate which logout_url to use"""
    remote_logouturl = remote_user.get_logouturl(request)
    if remote_logouturl and remote_logouturl.endswith('='):
        remote_logouturl += request.build_absolute_uri(LOGOUT_URL)
    return remote_logouturl if remote_logouturl else LOGOUT_URL


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

        remote_username = remote_user.get_username(request)
        if remote_username:
            _logger.debug(
                ('AuthenticationMiddleware: ' '(REMOTE_USER: "%s") from "%s"'),
                remote_username,
                request.get_full_path(),
            )
            if logged_in.id == Account.DEFAULT_ACCOUNT:
                # Switch from anonymous to REMOTE_USER
                remote_user.login(request)
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
