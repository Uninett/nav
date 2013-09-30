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
"""Models for the NAV API"""

from django.db import models
from nav.models.fields import VarcharField
from nav.models.profiles import Account


class APIToken(models.Model):
    """APItokens are used for authenticating to the api"""
    token = VarcharField()
    expires = models.DateTimeField()
    client = models.ForeignKey(Account, db_column='client')
    scope = models.IntegerField(null=True, default=0)

    def __unicode__(self):
        return self.token

    class Meta:
        db_table = 'apitoken'
