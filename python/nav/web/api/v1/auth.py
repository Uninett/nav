#
# Copyright (C) 2013 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Contains authentication and authorization code for API"""

import logging
from datetime import datetime
from django.utils.six.moves.urllib.parse import urlparse
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import (TokenAuthentication,
                                           BaseAuthentication)

from nav.models.api import APIToken

_logger = logging.getLogger(__name__)


ALLOWED_METHODS = ['GET']


class APIAuthentication(TokenAuthentication):
    """Authenticates API users"""

    def authenticate_credentials(self, key):
        """Checks for valid token"""
        _logger.debug('Authenticating credentials with %s', key)
        try:
            token = APIToken.objects.get(token=key)
        except APIToken.DoesNotExist:
            _logger.warning(
                'API authentication attempted with non-existing token "%s"',
                key)
            raise AuthenticationFailed
        else:
            if token.is_expired():
                _logger.warning(
                    'API authentication attempted with expired token "%s"', key)
                raise AuthenticationFailed
            return None, token


class NavBaseAuthentication(BaseAuthentication):
    """Returns logged in user"""

    def authenticate(self, request):
        _logger.debug("Baseauthentication account is %s", request.account)
        if request.account and not request.account.is_default_account():
            return request.account, None


class APIPermission(BasePermission):
    """Checks for correct permissions when accessing the API"""

    def has_permission(self, request, _):
        """Checks if request is permissable
        :type request: rest_framework.request.Request
        """
        if request.method not in ALLOWED_METHODS:
            _logger.warning('API access with forbidden method - %s',
                            request.method)
            return False

        # If user is logged in, it is authorized
        if not request.account.is_default_account():
            _logger.debug('User is logged in and thus authorized')
            return True

        token = request.auth  # type: APIToken
        _logger.debug('Token: %r', token)
        if token:
            if token_has_permission(request, token):
                token.last_used = datetime.now()
                token.save()
                return True
            else:
                _logger.warning(
                    'Token %s not permitted to access endpoint %s',
                    token, request.path)

        return False


def token_has_permission(request, token):
    """Verify that this token has permission to access the request path
    :type request: rest_framework.request.Request
    :type token: APIToken

    NB: This will fail if the version is not specified in the request url
    """
    if token.endpoints:
        request_path = ensure_trailing_slash(request.path)
        return any([request_path.startswith(
            ensure_trailing_slash(urlparse(endpoint).path))
                    for endpoint in token.endpoints.values()])
    return False


def ensure_trailing_slash(path):
    """Ensure that the path ends with a slash
    :type path: str
    """
    return path if path.endswith('/') else path + '/'
