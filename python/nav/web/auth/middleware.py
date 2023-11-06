# Copyright (C) 2010, 2011, 2013, 2019 Uninett AS
# Copyright (C) 2022, 2023 Sikt
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
Django middleware for handling login, authentication and authorization for NAV.
"""

import logging
import os

from django.http import HttpResponseRedirect, HttpResponse

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django <= 1.9
    MiddlewareMixin = object

from nav.models.profiles import Account
from nav.web.auth import remote_user, get_login_url, logout
from nav.web.auth.utils import (
    ensure_account,
    authorization_not_required,
)
from nav.web.auth.sudo import get_sudoer


_logger = logging.getLogger(__name__)


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
