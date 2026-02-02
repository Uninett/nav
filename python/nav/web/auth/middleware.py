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
from typing import Optional

from django.contrib.auth.middleware import RemoteUserMiddleware
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.utils.deprecation import MiddlewareMixin
from django_htmx.http import HttpResponseClientRedirect

from nav.web.auth import remote_user, get_login_url
from nav.web.auth.utils import (
    authorization_not_required,
    default_account,
    ensure_account,
    get_account,
)
from nav.web.auth.sudo import get_sudoer
from nav.web.utils import is_ajax


_logger = logging.getLogger(__name__)


class AuthorizationMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The NAV Django authentication middlewares requires Django's "
                "auth middleware to be installed. Edit your MIDDLEWARE setting "
                "to insert "
                "'django.contrib.auth.middleware.AuthenticationMiddleware' "
                "before 'nav.web.auth.middleware.AuthorizationMiddleware'."
            )
        account = get_account(request)

        authorized = authorization_not_required(
            request.get_full_path()
        ) or account.has_perm('web_access', request.get_full_path())
        if not authorized:
            _logger.warning(
                "User %s denied access to %s", account.login, request.get_full_path()
            )
            return self.redirect_to_login(request)

    def redirect_to_login(self, request: HttpRequest) -> HttpResponse:
        """Redirects a request to the NAV login page, unless it was detected
        to be an AJAX request, in which case return a 401 Not Authorized
        response.

        """
        if is_ajax(request):
            return HttpResponse(status=401)

        if request.htmx:
            if orig_path := request.htmx.current_url_abs_path:
                new_url = get_login_url(request, path=orig_path)
                return HttpResponseClientRedirect(new_url)
            else:
                return HttpResponse(status=401)

        new_url = get_login_url(request)
        return HttpResponseRedirect(new_url)


class NAVRemoteUserMiddleware(RemoteUserMiddleware):
    "Adapt Django's RemoteUserMiddleware to NAV's settings"

    _logger = logging.getLogger(f'{__name__}.NAVRemoteUserMiddleware')

    def __init__(self, get_response):
        self.header = remote_user.CONFIG.get_remote_user_varname()
        self.force_logout_if_no_header = (
            remote_user.CONFIG.will_force_logout_if_no_header()
        )
        super().__init__(get_response)

    def process_request(self, request):
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The NAV Django authentication middlewares requires Django's "
                "auth middleware to be installed. Edit your MIDDLEWARE setting "
                "to insert "
                "'django.contrib.auth.middleware.AuthenticationMiddleware' "
                "before 'nav.web.auth.middleware.NAVRemoteUserMiddleware'."
            )

        if not remote_user.CONFIG.is_remote_user_enabled():
            self._logger.debug(
                'NAVRemoteUserMiddleware is skipped, turned off in NAV settings',
            )
            return None

        path = request.get_full_path()
        existing_user = request.user
        self._logger.debug(
            'ENTER (session: %s, account: %s) from "%s"',
            dict(request.session),
            existing_user,
            path,
        )

        self._logger.debug(
            'request.META["REMOTE_USER"]: "%s"',
            request.META.get("REMOTE_USER", "NOT SET"),
        )
        next = super().process_request(request)
        remote_userobj = get_account(request)
        self._logger.debug(
            'REMOTE_USER: "%s" from "%s"',
            remote_userobj.get_username(),
            path,
        )
        self._logger.debug('NEXT %s', next)
        self._logger.debug(
            'EXIT (session: %s, account: %s) from "%s"',
            dict(request.session),
            remote_userobj.get_username(),
            path,
        )
        return next


class NAVAuthenticationMiddleware(MiddlewareMixin):
    """Use NAV's AnonymousUser and handle sudo

    Designed to run after AuthenticationMiddleware and NAVRemoteUserMiddleware
    """

    _logger = logging.getLogger(f"{__name__}.NAVAuthenticationMiddleware")

    def process_request(self, request: HttpRequest) -> None:
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The NAV Django authentication middlewares requires Django's "
                "auth middleware to be installed. Edit your MIDDLEWARE setting "
                "to insert "
                "'django.contrib.auth.middleware.AuthenticationMiddleware' "
                "before 'nav.web.auth.middleware.NAVAuthenticationMiddleware'."
            )

        account = request.user
        self._logger.debug(
            'ENTER (session: %s, account: %s) from "%s"',
            dict(request.session),
            account,
            request.get_full_path(),
        )

        # Ensure user is set correctly
        ensure_account(request)
        self._logger.debug(
            'Account ensured: (session: %s, account: %s) from "%s"',
            dict(request.session),
            request.user,
            request.get_full_path(),
        )

        # Set sudo
        sudo_operator = get_sudoer(request)  # Account or None

        if sudo_operator is not None:
            if isinstance(request.user, AnonymousUser):
                account = default_account()
                request.user = account
            # XXX: sudo: Account.sudo_operator should be set by function!
            request.user.sudo_operator = sudo_operator
            request.account = request.user
            self._logger.debug(
                'SUDO! "%s" acting as "%s"',
                sudo_operator.get_username(),
                account.get_username(),
            )
        else:
            self._logger.debug('No sudo')

        self._logger.debug(
            'EXIT (session: %s, account: %s) from "%s"',
            dict(request.session),
            request.user,
            request.get_full_path(),
        )
