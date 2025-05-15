# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2011 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
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
from nav.models.fields import VarcharField


class Cabling(models.Model):
    """From NAV Wiki: The cabling table documents the cabling from the wiring
    closet's jack number to the end user's room number."""

    id = models.AutoField(db_column='cablingid', primary_key=True)
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        db_column='roomid',
        related_name="cabling_set",
    )
    jack = VarcharField()
    building = VarcharField(blank=True)
    target_room = VarcharField(db_column='targetroom', blank=True)
    description = VarcharField(db_column='descr', blank=True)
    category = VarcharField(blank=True)

    class Meta(object):
        db_table = 'cabling'
        unique_together = (('room', 'jack'),)

    def __str__(self):
        return 'jack %s, in room %s' % (self.jack, self.room.id)

    def verbose(self):
        """Returns a more verbose description of this cable"""
        return 'jack {}'.format(
            ", ".join(
                [
                    x
                    for x in [
                        self.jack,
                        self.building,
                        self.target_room,
                        self.description,
                    ]
                    if x
                ]
            )
        )


class Patch(models.Model):
    """From NAV Wiki: The patch table documents the cross connect from switch
    port to jack."""

    id = models.AutoField(db_column='patchid', primary_key=True)
    interface = models.ForeignKey(
        Interface,
        on_delete=models.CASCADE,
        db_column='interfaceid',
        related_name='patches',
    )
    cabling = models.ForeignKey(
        Cabling,
        on_delete=models.CASCADE,
        db_column='cablingid',
        related_name='patches',
    )
    split = VarcharField(default='no')

    class Meta(object):
        db_table = 'patch'
        unique_together = (('interface', 'cabling'),)

    def __str__(self):
        return '%s, patched to %s' % (self.interface, self.cabling)
