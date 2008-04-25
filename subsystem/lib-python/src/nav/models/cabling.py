# -*- coding: utf-8 -*-
#
# Copyright 2007 UNINETT AS
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
# Authors: Stein Magnus Jodal <stein.magnus.jodal@uninett.no>
#

"""Django ORM wrapper for the NAV manage database"""

__copyright__ = "Copyright 2007 UNINETT AS"
__license__ = "GPL"
__author__ = "Stein Magnus Jodal (stein.magnus.jodal@uninett.no)"
__id__ = "$Id$"

from django.db import models

from nav.models.manage import Room, SwPort

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
    swport = models.ForeignKey(SwPort, db_column='swportid')
    cabling = models.ForeignKey(Cabling, db_column='cablingid')
    split = models.CharField(max_length=-1, default='no')

    class Meta:
        db_table = 'patch'
        unique_together = (('swport', 'cabling'),)

    def __unicode__(self):
        return u'%s, patched to %s' % (self.swport, self.cabling)
