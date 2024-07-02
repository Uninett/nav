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
"""

from datetime import datetime
import logging

from urllib import parse

from django.urls import reverse

from nav.auditlog.models import LogEntry
from nav.models.profiles import Account, AccountGroup
from nav.web.auth import ldap, remote_user
from nav.web.auth.sudo import desudo
from nav.web.auth.utils import clear_session


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

    # Try to find the account in the database. If it's not found we can try
    # LDAP.
    try:
        account = Account.objects.get(login__iexact=username)
    except Account.DoesNotExist:
        # account autocreated if username is authenticated
        account = ldap.authenticate(username, password)
        return account

    if account.locked:
        _logger.info("Locked user %s tried to log in", account.login)
        return None

    if account.ext_sync == 'ldap' and ldap.available:
        try:
            ldap_user = ldap.get_ldap_user(username, password)
        except ldap.NoAnswerError:
            pass
        else:
            if ldap_user:
                account = ldap.update_ldap_user(ldap_user, account, password)
                return account
            return None
        # Fallback to stored password if ldap is unavailable

    if account.check_password(password):
        return account
    return None


def get_login_url(request):
    """Calculate which login_url to use"""
    path = parse.quote(request.get_full_path())
    if path == "/":
        default_new_url = LOGIN_URL
    else:
        default_new_url = '{0}?origin={1}&noaccess'.format(LOGIN_URL, path)
    remote_loginurl = remote_user.get_loginurl(request)
    return remote_loginurl if remote_loginurl else default_new_url


def get_post_logout_redirect_url(request):
    default = "/"
    redirect_url = remote_user.get_post_logout_redirect_url(request)
    return redirect_url if redirect_url else default


def get_logout_url(request):
    """Calculate which logout_url to use"""
    remote_logouturl = remote_user.get_logouturl(request)
    if remote_logouturl and remote_logouturl.endswith('='):
        remote_logouturl += request.build_absolute_uri(LOGOUT_URL)
    return remote_logouturl if remote_logouturl else LOGOUT_URL


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
        clear_session(request)
        _logger.debug('logout: logout %s', account.login)
        LogEntry.add_log_entry(account, 'log-out', '{actor} logged out', before=account)
    _logger.debug('logout: redirect to "/" after logout')
    return get_post_logout_redirect_url(request)
