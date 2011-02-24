# -*- coding: utf-8 -*-
#
# Copyright 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
__copyright__ = "Copyright 2011 UNINETT AS"
__license__ = "GPL"
__author__ = "John-Magne Bredal <john.m.bredal@ntnu.no> and Trond Kandal <Trond.Kandal@ntnu.no>"
__id__ = "$Id$"


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
