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
Support logging in by having the web server set the REMOTE_USER header.
"""

import logging
from os.path import join
import secrets

from nav.auditlog.models import LogEntry
from nav.config import NAVConfigParser
from nav.models.profiles import Account
from nav.web.auth.utils import set_account


__all__ = []


class RemoteUserConfigParser(NAVConfigParser):
    DEFAULT_CONFIG_FILES = [join('webfront', 'webfront.conf')]
    DEFAULT_CONFIG = """
[remote-user]
enabled=no
login-url=
logout-url=
varname=REMOTE_USER
workaround=none
autocreate=off
post-logout-redirect-url=/
"""


_logger = logging.getLogger(__name__)
_config = RemoteUserConfigParser()


def fake_password(length):
    return secrets.token_urlsafe(length)


def authenticate(request):
    """Authenticate username from http header REMOTE_USER

    Returns:

    :return: If the user was authenticated, an account.
             If the user was blocked from logging in, False.
             Otherwise, None.
    :rtype: Account, False, None
    """
    username = get_username(request)
    if not username:
        return None

    # We now have a username-ish

    try:
        account = Account.objects.get(login=username)
    except Account.DoesNotExist:
        if _config.getboolean('remote-user', 'autocreate', fallback=False):
            return autocreate_remote_user(username)
        # Bail out!
        _logger.info('User creation turned off, did not create "%s"', username)
        return False

    # Bail out! Potentially evil user
    if account.locked:
        _logger.info("Locked user %s tried to log in", account.login)
        template = 'Account "{actor}" was prevented from logging in: blocked'
        LogEntry.add_log_entry(
            account, 'login-prevent', template=template, subsystem='auth'
        )
        return False

    return account


def autocreate_remote_user(username):
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


def login(request):
    """Log in the user in REMOTE_USER, if any and enabled

    :return: Account for remote user, or None
    :rtype: Account, None
    """
    remote_username = get_username(request)
    if remote_username:
        # Get or create an account from the REMOTE_USER http header
        account = authenticate(request)
        if account:
            set_account(request, account)
            return account
    return None


def get_loginurl(request):
    """Return a url (if set) to log in to/via a remote service

    :return: Either a string with an url, or None.
    :rtype: str, None
    """
    return get_remote_url(request, 'login-url')


def get_logouturl(request):
    """Return a url (if set) to log out to/via a remote service

    :return: Either a string with an url, or None.
    :rtype: str, None
    """
    return get_remote_url(request, 'logout-url')


def get_post_logout_redirect_url(request):
    """Return a url (if set) to log out to/via a remote service

    :return: Either a string with an url, or None.
    :rtype: str, None
    """
    return get_remote_url(request, "post-logout-redirect-url")


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


def get_username(request):
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
