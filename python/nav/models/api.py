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
"""Models for the NAV API"""

from datetime import datetime, timedelta
from typing import Dict, Any

import jwt

from django.db import models
from django.urls import reverse

from nav.adapters import HStoreField
from nav.models.fields import VarcharField
from nav.models.profiles import Account
from nav.jwtconf import JWTConf


class APIToken(models.Model):
    """APItokens are used for authenticating to the api

    Endpoints may be connected to the token in which case the token also works
    as an authorization token.
    """

    permission_choices = (('read', 'Read'), ('write', 'Write'))
    permission_help_text = "Read means that this token can be used for reading only. Write means that this token can be used to create new, update and delete objects as well as reading."

    token = VarcharField()
    expires = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    client = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        db_column='client',
        related_name="api_tokens",
    )
    scope = models.IntegerField(null=True, default=0)
    comment = models.TextField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    last_used = models.DateTimeField(null=True)
    endpoints = HStoreField(null=True, blank=True, default=dict)
    permission = VarcharField(
        choices=permission_choices, help_text=permission_help_text, default='read'
    )

    def __str__(self):
        return self.token

    def is_expired(self):
        """Check is I am expired"""
        return self.expires < datetime.now()

    def get_absolute_url(self):
        """Special method that Django uses as default url for an object"""
        return reverse('useradmin-token_detail', args=[self.pk])

    class Meta(object):
        db_table = 'apitoken'


class JWTRefreshToken(models.Model):
    """RefreshTokens are used for generating new access tokens"""

    token = VarcharField()
    name = VarcharField(unique=True)
    description = models.TextField(null=True, blank=True)

    ACCESS_EXPIRE_DELTA = timedelta(hours=1)
    REFRESH_EXPIRE_DELTA = timedelta(days=1)

    def __str__(self):
        return self.token

    @property
    def data(self) -> Dict[str, Any]:
        """Body of token as a dict"""
        return self.decode_token(self.token)

    @property
    def nbf(self) -> datetime:
        """Datetime when token activates"""
        return datetime.fromtimestamp(self.data['nbf'])

    @property
    def exp(self) -> datetime:
        """Datetime when token expires"""
        return datetime.fromtimestamp(self.data['exp'])

    @property
    def is_active(self) -> bool:
        """True if token is active. A token is considered active when
        the nbf claim is in the past and the exp claim is in the future
        """
        now = datetime.now()
        return now >= self.nbf and now < self.exp

    def expire(self):
        """Expires the token"""
        # Base claims for expired token on existing claims
        expired_data = self.data
        expired_data['exp'] = datetime.now().timestamp()
        expired_data['nbf'] = datetime.now().timestamp()
        self.token = self._encode_token(expired_data)
        self.save()

    @classmethod
    def _encode_token(cls, token_data: Dict[str, Any]) -> str:
        """Returns an encoded token in JWT format"""
        return jwt.encode(
            token_data, JWTConf().get_nav_private_key(), algorithm="RS256"
        )

    @classmethod
    def _generate_token(
        cls, token_data: Dict[str, Any], expiry_delta: timedelta, token_type: str
    ) -> str:
        """Generates and returns a token in JWT format. Will use `token_data` as a basis
        for the new token, but certain claims will be overridden
        """
        new_token = dict(token_data)
        now = datetime.now()
        name = JWTConf().get_nav_name()
        updated_claims = {
            'exp': (now + expiry_delta).timestamp(),
            'nbf': now.timestamp(),
            'iat': now.timestamp(),
            'aud': name,
            'iss': name,
            'token_type': token_type,
        }
        new_token.update(updated_claims)
        return cls._encode_token(new_token)

    @classmethod
    def generate_access_token(cls, token_data: Dict[str, Any] = {}) -> str:
        """Generates and returns an access token in JWT format. Will use `token_data` as a basis
        for the new token, but certain claims will be overridden
        """
        return cls._generate_token(token_data, cls.ACCESS_EXPIRE_DELTA, "access_token")

    @classmethod
    def generate_refresh_token(cls, token_data: Dict[str, Any] = {}) -> str:
        """Generates and returns a refresh token in JWT format. Will use `token_data` as a basis
        for the new token, but certain claims will be overridden
        """
        return cls._generate_token(
            token_data, cls.REFRESH_EXPIRE_DELTA, "refresh_token"
        )

    @classmethod
    def decode_token(cls, token: str) -> Dict[str, Any]:
        """Decodes a token in JWT format and returns the body of the decoded token"""
        return jwt.decode(token, options={'verify_signature': False})

    class Meta(object):
        db_table = 'jwtrefreshtoken'
