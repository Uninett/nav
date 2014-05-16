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

from datetime import datetime
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import TokenAuthentication

from nav.models.api import APIToken

ALLOWED_METHODS = ['GET']


class APIAuthentication(TokenAuthentication):
    """Authenticates API users"""

    def authenticate_credentials(self, key):
        """Checks for valid token"""
        try:
            token = APIToken.objects.get(token=key, expires__gt=datetime.now())
        except APIToken.DoesNotExist:
            raise AuthenticationFailed
        else:
            return None, token


class APIPermission(BasePermission):
    """Checks for correct permissions when accessing the API"""

    def has_permission(self, request, _):
        """Checks if request is permissable"""
        if request.method not in ALLOWED_METHODS:
            return False

        token = request.auth
        if not token:
            return False

        # If the token exists we have already done a verification for it
        # in the authentication
        return True
