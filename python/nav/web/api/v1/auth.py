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
from urlparse import urlparse
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
            token = APIToken.objects.get(token=key, expires__gt=datetime.now())
        except APIToken.DoesNotExist:
            raise AuthenticationFailed
        else:
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
        """Checks if request is permissable"""
        if request.method not in ALLOWED_METHODS:
            return False

        _logger.debug("request.user: %r", request.user)
        _logger.debug("request.auth: %r", request.auth)

        # If user is logged in, it is authorized
        if not request.account.is_default_account():
            return True

        token = request.auth
        if token:
            # Compare registered token endpoints with request path
            return token_has_permission(request, token)

        return False


def token_has_permission(request, token_hash):
    """Verify that this token has permission to access the path"""
    try:
        token = APIToken.objects.get(token=token_hash)
    except APIToken.DoesNotExist:
        return False
    else:
        if token.endpoints:
            request_path = ensure_trailing_slash(request.path)
            return any([request_path.startswith(
                ensure_trailing_slash(urlparse(endpoint).path))
                        for endpoint in token.endpoints.values()])
    return False


def ensure_trailing_slash(path):
    """Ensure that the path ends with a slash"""
    return path if path.endswith('/') else path + '/'
