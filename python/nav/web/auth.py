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
Contains web authentication functionality for NAV.
"""
"""NAV authentication and authorization middleware for Django"""
"""
Authentication and authorization middleware for Django.
"""

from datetime import datetime
import logging
from os.path import join
import os

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.six.moves.urllib import parse

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django <= 1.9
    MiddlewareMixin = object


_logger = logging.getLogger(__name__)

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


ACCOUNT_ID_VAR = 'account_id'
SUDOER_ID_VAR = 'sudoer'

# This may seem like redundant information, but it seems django's reverse
# will hang under some usages of these middleware classes - so until we figure
# out what's going on, we'll hardcode this here.
LOGIN_URL = '/index/login/'


class RemoteUserConfigParser(NAVConfigParser):
    DEFAULT_CONFIG_FILES = [join('webfront', 'webfront.conf')]
    DEFAULT_CONFIG = u"""
[remote-user]
enabled=no
login-url=
"""
_config = RemoteUserConfigParser()


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


def authenticate_remote_user(request=None):
    """Authenticate username from http header REMOTE_USER

    Returns:

    * account object if user was authenticated
    * False if authenticated but blocked from logging in
    * None in all other cases
    """
    username = get_remote_username(request)
    if not username:
        return None

    # We now have a username-ish

    try:
        account = Account.objects.get(login=username)
    except Account.DoesNotExist:
        # Store the remote user in the database and return the new account
        account = Account(
            login=username,
            name=username,
            ext_sync='REMOTE_USER'
        )
        account.set_password(fake_password(32))
        account.save()
        _logger.info("Created user %s from header REMOTE_USER", account.login)
        template = 'Account "{actor}" created due to REMOTE_USER HTTP header'
        LogEntry.add_log_entry(account, 'create-account', template=template,
                               subsystem='auth')
        return account

    # Bail out! Potentially evil user
    if account.locked:
        _logger.info("Locked user %s tried to log in", account.login)
        template = 'Account "{actor}" was prevented from logging in: blocked'
        LogEntry.add_log_entry(account, 'login-prevent', template=template,
                               subsystem='auth')
        return False

    return account


def get_login_url(request):
    """Calculate which login_url to use"""
    default_new_url = '{0}?origin={1}&noaccess'.format(
        LOGIN_URL,
        parse.quote(request.get_full_path()))
    remote_loginurl = get_remote_loginurl(request)
    return remote_loginurl if remote_loginurl else default_new_url


def get_remote_loginurl(request):
    """Return a url (if set) to a remote service for REMOTE_USER purposes

    Return None if no suitable url is available or enabled.
    """
    remote_login_url = None
    try:
        if not _config.getboolean('remote-user', 'enabled'):
            return None
        remote_login_url = _config.get('remote-user', 'login-url')
    except ValueError:
        return None
    if remote_login_url:
        nexthop = request.build_absolute_uri(request.get_full_path())
        remote_login_url = remote_login_url.format(nexthop)
    return remote_login_url


def get_remote_username(request):
    """Return the username in REMOTE_USER if set and enabled

    Return None otherwise.
    """
    try:
        if not _config.getboolean('remote-user', 'enabled'):
            return None
    except ValueError:
        return None

    if not request:
        return None

    username = request.META.get('REMOTE_USER', '').strip()
    if not username:
        return None

    return username


def login_remote_user(request):
    """Log in the user in REMOTE_USER, if any and enabled

    Returns None otherwise
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


# Middleware


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        session = request.session
        account = getattr(request, 'account', None)

        if ACCOUNT_ID_VAR not in session:  # Not logged in
            # Fallback: Set account id to anonymous user
            session[ACCOUNT_ID_VAR] = Account.DEFAULT_ACCOUNT
            # Try remote user
            login_remote_user(request)
            account = getattr(request, 'account', None)

        if not account or account.id != session[ACCOUNT_ID_VAR]:
            # Reget account if:
            # * account not set
            # * account.id different from session[ACCOUNT_ID_VAR]
            account = Account.objects.get(id=session[ACCOUNT_ID_VAR])

        remote_username = get_remote_username(request)
        if remote_username and remote_username != account.login:
            # REMOTE_USER has changed behind your back
            # Log out current user, log in new user
            logout(request)
            login_remote_user(request)
            account = getattr(request, 'account', None)

        # Now we have an account
        request.account = account

        if SUDOER_ID_VAR in session:
            account.sudo_operator = get_sudoer(request)

        _logger.debug("Request for %s authenticated as user=%s",
                      request.get_full_path(), account.login)


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

        new_url = get_login_url(request)
        return HttpResponseRedirect(new_url)


def authorization_not_required(fullpath):
    """Checks is authorization is required for the requested url

    Should the user be able to decide this? Currently not.

    """
    auth_not_required = ['/api/', '/doc/']
    for url in auth_not_required:
        if fullpath.startswith(url):
            return True


def logout(request):
    """Log out a user from a request

    Returns a safe, public path useful for callers building a redirect."""
    if request.method == 'POST' and 'submit_desudo' in request.POST:
        desudo(request)
        return reverse('webfront-index')
    else:
        account = request.account
        del request.session[ACCOUNT_ID_VAR]
        del request.account
        request.session.set_expiry(datetime.now())
        request.session.save()
        LogEntry.add_log_entry(account, 'log-out', '{actor} logged out',
                               before=account)
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
    request.session[SUDOER_ID_VAR] = request.account.id
    request.session[ACCOUNT_ID_VAR] = other_user.id
    request.session.save()
    request.account = other_user


def desudo(request):
    """Switches the current session to become the original user from before a
    call to sudo().

    """
    if SUDOER_ID_VAR not in request.session:
        # We are not sudoing
        return

    original_user_id = request.session[SUDOER_ID_VAR]
    original_user = Account.objects.get(id=original_user_id)

    del request.session[ACCOUNT_ID_VAR]
    del request.session[SUDOER_ID_VAR]
    request.session[ACCOUNT_ID_VAR] = original_user_id
    request.session.save()
    request.account = original_user


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
