# -*- coding: utf-8 -*-
#
# Copyright 2008 NTNU
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
# Authors: John-Magne Bredal <john.m.bredal@ntnu.no>
#

from django.db import models
from nav.models.manage import Cam

class MacWatch(models.Model):
    """ Store watched mac-addresses """

    id = models.AutoField(primary_key=True)
    cam = models.ForeignKey(Cam, db_column='camid')
    mac = models.CharField(max_length=17)
    posted = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey('Account', db_column='userid')
    login = models.CharField()
    description = models.CharField()

    class Meta:
        db_table = 'macwatch'

    def __unicode__(self):
        return self.mac

class Account(models.Model):
    """ Account information for NAV users """

    id = models.AutoField(primary_key=True)
    login = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=50, null=True)
    password = models.CharField(max_length=30, null=True)
    ext_sync = models.CharField(max_length=30, null=True)

    class Meta:
        db_table = 'account'

    def __unicode__(self):
        return self.login
