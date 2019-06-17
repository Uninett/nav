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

from django.db import models
from django.urls import reverse
from django.utils.encoding import python_2_unicode_compatible

from nav.adapters import HStoreField
from nav.models.fields import VarcharField
from nav.models.profiles import Account


@python_2_unicode_compatible
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
        db_column='client'
    )
    scope = models.IntegerField(null=True, default=0)
    comment = models.TextField(null=True, blank=True)
    revoked = models.BooleanField(default=False)
    last_used = models.DateTimeField(null=True)
    endpoints = HStoreField(null=True, blank=True, default=dict)
    permission = VarcharField(choices=permission_choices,
                              help_text=permission_help_text,
                              default='read')

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
