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
import re

from django.contrib.auth import SESSION_KEY as DJANGO_USER_SESSION_KEY
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject

from nav.django.defaults import PUBLIC_URLS
from nav.models.profiles import Account


_logger = logging.getLogger(__name__)


ACCOUNT_ID_VAR = 'account_id'
PASSWORD_ISSUES_CACHE_KEY = "auth:accounts_password_issues"


def default_account():
    """
    Returns the user representing an unauthenticated account

    default_account().is_anonymous is always True.
    default_account().is_default_account() always returns True.
    """
    return Account.objects.get(id=Account.DEFAULT_ACCOUNT)


def get_account(request):
    """Returns the account associated with the request"""
    try:
        return request.account
    except AttributeError:
        pass
    try:
        return request.user
    except AttributeError:
        return default_account()


def set_account(request, account, cycle_session_id=True):
    """Updates request with new account.
    Cycles the session ID by default to avoid session fixation.
    """
    request.session[ACCOUNT_ID_VAR] = account.id
    request.session[DJANGO_USER_SESSION_KEY] = str(account.id)
    request.account = request._cached_user = account
    request.user = SimpleLazyObject(lambda: account)
    _logger.debug('Set active account to "%s"', account.login)
    if cycle_session_id:
        request.session.cycle_key()
    request.session.save()


def clear_session(request):
    """Clears the session and logs out the current account"""
    if hasattr(request, "account"):
        del request.account
    if hasattr(request, "user"):
        del request.user
    request.session.flush()
    request.session.save()


def ensure_account(request):
    """Guarantee that valid request.account is set"""
    if request.user.id:
        account = Account.objects.get(id=request.user.id)
    else:
        account = Account.objects.get(id=Account.DEFAULT_ACCOUNT)

    if account.locked and not account.is_default_account():
        # logout of locked account
        clear_session(request)

        # Switch back to fallback, the anonymous user
        # Assumes nobody has locked it..
        account = default_account()

    # Do not cycle to avoid session_id being changed on every request
    set_account(request, account, cycle_session_id=False)


def authorization_not_required(fullpath):
    """Checks is authorization is required for the requested url

    Should the user be able to decide this? Currently not.

    """
    for url in PUBLIC_URLS:
        if fullpath.startswith(url):
            _logger.debug('authorization_not_required: %s', url)
            return True
    auth_not_required_regex = [r'^/index/dashboard/[^/]+/load/?$']
    for regex in auth_not_required_regex:
        if re.match(regex, fullpath):
            _logger.debug('authorization_not_required: %s', regex)
            return True
    return False


def get_number_of_accounts_with_password_issues() -> int:
    """
    Returns the number of accounts that have password issues like old style password
    hashes, plaintext passwords or deprecated password hash methods
    """
    number_of_accounts_with_password_issues = cache.get(
        PASSWORD_ISSUES_CACHE_KEY, default=None
    )
    if number_of_accounts_with_password_issues is None:
        number_of_accounts_with_password_issues = 0
        for account in Account.objects.all():
            if account.has_password_issues():
                number_of_accounts_with_password_issues += 1
        cache.set(PASSWORD_ISSUES_CACHE_KEY, number_of_accounts_with_password_issues)

    return number_of_accounts_with_password_issues
