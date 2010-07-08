# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Django ORM wrapper for the NAV manage database"""

from django.db import models

from nav.models.manage import Room, Interface

class Cabling(models.Model):
    """From MetaNAV: The cabling table documents the cabling from the wiring
    closet's jack number to the end user's room number."""

    id = models.AutoField(db_column='cablingid', primary_key=True)
    room = models.ForeignKey(Room, db_column='roomid')
    jack = models.CharField(max_length=-1)
    building = models.CharField(max_length=-1)
    target_room = models.CharField(db_column='targetroom', max_length=-1)
    description = models.CharField(db_column='descr', max_length=-1)
    category = models.CharField(max_length=-1)

    class Meta:
        db_table = 'cabling'
        unique_together = (('room', 'jack'),)

    def __unicode__(self):
        return u'jack %s, in room %s' % (self.jack, self.room.id)

class Patch(models.Model):
    """From MetaNAV: The patch table documents the cross connect from switch
    port to jack."""

    id = models.AutoField(db_column='patchid', primary_key=True)
    interface = models.ForeignKey(Interface, db_column='interfaceid')
    cabling = models.ForeignKey(Cabling, db_column='cablingid')
    split = models.CharField(max_length=-1, default='no')

    class Meta:
        db_table = 'patch'
        unique_together = (('interface', 'cabling'),)

    def __unicode__(self):
        return u'%s, patched to %s' % (self.interface, self.cabling)
