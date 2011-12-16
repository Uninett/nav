#
# Copyright (C) 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""macwatch Django models"""

from django.db import models
from nav.models.fields import VarcharField
from nav.models.manage import Cam
from nav.models.profiles import Account

class MacWatch(models.Model):
    id = models.AutoField(db_column='id', primary_key=True)
    camid = models.ForeignKey(Cam, db_column='camid', null=True)
    # TODO: Create MACAddressField in Django
    mac = models.CharField(max_length=17, unique=True)
    created = models.DateTimeField(auto_now_add=True)
    posted = models.DateTimeField()
    userid = models.ForeignKey(Account, db_column='userid', null=True)
    description = VarcharField()

    class Meta:
        db_table = u'macwatch'
        ordering = ('created',)

    def __unicode__(self):
        return u'%s' % self.mac
