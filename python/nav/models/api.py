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

from datetime import datetime

from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.urls import reverse

from nav.models.fields import VarcharField
from nav.models.profiles import Account
from nav.web.jwtgen import is_active


class APIToken(models.Model):
    """APItokens are used for authenticating to the api

    Endpoints may be connected to the token in which case the token also works
    as an authorization token.
    """

    permission_choices = (('read', 'Read'), ('write', 'Write'))
    permission_help_text = (
        "Read means that this token can be used for reading only. Write means that "
        "this token can be used to create new, update and delete objects as well as "
        "reading."
    )

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
    """Model representing a JWT refresh token. This model does not
    contain the token itself, but a hash of the token that can be used
    to validate the authenticity of the actual token when it is used to
    generate an access token.
    """

    permission_choices = (('read', 'Read'), ('write', 'Write'))
    permission_help_text = (
        "Read means that this token can be used for reading only. Write means that "
        "this token can be used to create new, update and delete objects as well as "
        "reading."
    )

    name = VarcharField(unique=True)
    description = models.TextField(null=True, blank=True)
    expires = models.DateTimeField()
    activates = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    endpoints = HStoreField(null=True, blank=True, default=dict)
    permission = VarcharField(
        choices=permission_choices, help_text=permission_help_text, default='read'
    )
    hash = VarcharField()

    def __str__(self):
        return self.name

    def is_active(self) -> bool:
        """Returns True if the token is active. A token is considered active when
        `expires` is in the future and `activates` is in the past or matches
        the current time.
        """
        return is_active(self.expires.timestamp(), self.activates.timestamp())

    class Meta(object):
        """Meta class"""

        db_table = 'jwtrefreshtoken'
