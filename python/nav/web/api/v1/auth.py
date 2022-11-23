#
# Copyright (C) 2013 Uninett AS
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
"""Contains authentication and authorization code for API"""

import logging
from datetime import datetime
from urllib.parse import urlparse
import json
import jwt
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authentication import TokenAuthentication, BaseAuthentication
from oidc_auth.authentication import JSONWebTokenAuthentication
from oidc_auth.settings import api_settings

from nav.models.api import APIToken

_logger = logging.getLogger(__name__)


class APIAuthentication(TokenAuthentication):
    """Authenticates API users"""

    def authenticate_credentials(self, key):
        """Checks for valid token"""
        _logger.debug('Authenticating credentials with %s', key)
        try:
            token = APIToken.objects.get(token=key)
        except APIToken.DoesNotExist:
            _logger.warning(
                'API authentication attempted with non-existing token "%s"', key
            )
            raise AuthenticationFailed
        else:
            if token.is_expired():
                _logger.warning(
                    'API authentication attempted with expired token "%s"', key
                )
                raise AuthenticationFailed
            return None, token


class NavBaseAuthentication(BaseAuthentication):
    """Returns logged in user"""

    def authenticate(self, request):
        _logger.debug("Baseauthentication account is %s", request.account)
        if request.account and not request.account.is_default_account():
            return request.account, None


class JWTToken(dict):
    pass


class JWTAuthentication(JSONWebTokenAuthentication):
    REQUIRED_CLAIMS = ["exp", "nbf", "aud", "iss"]
    SUPPORTED_ALGORITHMS = ["RS256", "RS384", "RS512"]

    def authenticate(self, request):
        auth_result = super().authenticate(request)
        if auth_result:
            user, token = auth_result
            return user, JWTToken(token)
        else:
            return None

    def decode_jwt(self, jwt_value):
        kid = self.get_kid(jwt_value)
        try:
            validated_token = jwt.decode(
                jwt=jwt_value,
                algorithms=self.SUPPORTED_ALGORITHMS,
                key=self.get_public_key(kid),
                options={"require": self.REQUIRED_CLAIMS},
                audience=api_settings.OIDC_CLAIMS_OPTIONS['aud']['value'],
                issuer=self.issuer,
            )
            return validated_token
        except jwt.exceptions.PyJWTError as e:
            raise AuthenticationFailed(f"Error validating token: {e}")

    def get_kid(self, token):
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise AuthenticationFailed("Token must include the 'kid' header")
        return kid

    def get_public_key(self, kid):
        jwks = self.jwks_data()
        for jwk in jwks.get("keys"):
            if jwk["kid"] == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
        raise AuthenticationFailed(f"Invalid kid '{kid}'")

    def validate_claims(self, id_token):
        """Do nothing. All validation is done in decode_jwt"""
        return


class LoggedInPermission(BasePermission):
    """Checks if the user is logged in"""

    def has_permission(self, request, _view):
        """If user is logged in, it is authorized"""
        return not request.account.is_default_account()


class TokenPermission(BasePermission):
    """Checks if the token has correct permissions"""

    url_prefix = '/api'
    version = 1

    def has_permission(self, request, _view):
        token = request.auth  # type: APIToken
        if not token or not isinstance(token, APIToken):
            return False

        endpoints_ok = self._check_endpoints(request)
        req_method_ok = self._check_read_write(request)
        permissions_ok = endpoints_ok and req_method_ok

        if permissions_ok:
            token.last_used = datetime.now()
            token.save()
        else:
            _logger.warning(
                'Token %s not permitted to access endpoint %s', token, request.path
            )
        return permissions_ok

    @staticmethod
    def _check_endpoints(request):
        """Verify that this token has permission to access the request path
        :type request: rest_framework.request.Request
        :type token: APIToken

        NB: This will fail if the version is not specified in the request url
        """
        token = request.auth
        if not token.endpoints:
            return False

        return TokenPermission.is_path_in_endpoints(request.path, token.endpoints)

    @staticmethod
    def _check_read_write(request):
        """Verify that the token permission matches the method"""
        token = request.auth
        return token.permission == 'write' or request.method in SAFE_METHODS

    @staticmethod
    def is_path_in_endpoints(request_path, endpoints):
        """
        :param str request_path: the request path
        :param dict endpoints: the endpoints available for a token as a dict
        :return: if the path is in one of the endpoints for this token
        """
        # Create prefix for the current api version
        prefix = '/'.join([TokenPermission.url_prefix, str(TokenPermission.version)])
        # Cut prefix from path
        request_path = TokenPermission._ensure_trailing_slash(
            request_path.replace(prefix, '').replace(TokenPermission.url_prefix, '')
        )
        # Create a list of endpoints and remove prefix from them
        endpoints = [e.replace(prefix, '') for e in endpoints.values()]
        # Check if path is in one of the endpoints
        return any(
            [
                request_path.startswith(
                    TokenPermission._ensure_trailing_slash(urlparse(endpoint).path)
                )
                for endpoint in endpoints
            ]
        )

    @staticmethod
    def _ensure_trailing_slash(path):
        """Ensure that the path ends with a slash
        :type path: str
        """
        return path if path.endswith('/') else path + '/'


class JWTPermission(BasePermission):
    """Checks if the token has correct permissions"""

    url_prefix = '/api'
    version = 1

    def has_permission(self, request, _view):
        token = request.auth  # type: JWTToken
        if not token or not isinstance(token, JWTToken):
            return False
        return True


class APIPermission(BasePermission):
    """Checks for correct permissions when accessing the API"""

    def has_permission(self, request, view):
        """Checks if request is permissable
        :type request: rest_framework.request.Request
        """
        return (
            LoggedInPermission().has_permission(request, view)
            or TokenPermission().has_permission(request, view)
            or JWTPermission().has_permission(request, view)
        )


def get_user(self, token):
    return None
