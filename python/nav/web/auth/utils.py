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

from nav.models.profiles import Account


_logger = logging.getLogger(__name__)


ACCOUNT_ID_VAR = 'account_id'


def set_account(request, account, cycle_session_id=True):
    """Updates request with new account.
    Cycles the session ID by default to avoid session fixation.
    """
    request.session[ACCOUNT_ID_VAR] = account.id
    request.account = account
    _logger.debug('Set active account to "%s"', account.login)
    if cycle_session_id:
        request.session.cycle_key()
    request.session.save()


def clear_session(request):
    """Clears the session and logs out the current account"""
    if hasattr(request, "account"):
        del request.account
    request.session.flush()
    request.session.save()


def ensure_account(request):
    """Guarantee that valid request.account is set"""
    session = request.session

    account_id = session.get(ACCOUNT_ID_VAR, Account.DEFAULT_ACCOUNT)
    account = Account.objects.get(id=account_id)

    if account.locked:
        # logout of locked account
        clear_session(request)

        # Switch back to fallback, the anonymous user
        # Assumes nobody has locked it..
        account = Account.objects.get(id=Account.DEFAULT_ACCOUNT)

    # Do not cycle to avoid session_id being changed on every request
    set_account(request, account, cycle_session_id=False)


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
