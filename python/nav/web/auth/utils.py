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
Utilities for authentication/authorization in NAV that is independent of
login method.
"""
import logging

from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore

from nav.models.profiles import Account


_logger = logging.getLogger(__name__)


ACCOUNT_ID_VAR = 'account_id'


def _set_account(request, account):
    request.session[ACCOUNT_ID_VAR] = account.id
    request.account = account
    _logger.debug('Set active account to "%s"', account.login)
    request.session.save()


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
