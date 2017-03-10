# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2017 UNINETT AS
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
"""Models for racks and rack items"""

from django.db import models

from nav.models.fields import VarcharField
from nav.models.manage import Room, Sensor


class Rack(models.Model):
    """A physical rack placed in a room."""

    id = models.AutoField(primary_key=True, db_column='rackid')
    room = models.ForeignKey(Room, db_column='roomid')
    rackname = VarcharField(blank=True)
    ordering = models.IntegerField()

    class Meta(object):
        db_table = 'rack'

    def __unicode__(self):
        return self.rackname or self.rackid

    def sensors_left(self):
        return RackSensor.objects.filter(rack=self, col=0).order_by('row')

    def sensors_center(self):
        return RackSensor.objects.filter(rack=self, col=1).order_by('row')

    def sensors_right(self):
        return RackSensor.objects.filter(rack=self, col=2).order_by('row')


class RackSensor(models.Model):
    """A sensor placed in a rack"""

    id = models.AutoField(primary_key=True, db_column='racksensorid')
    rack = models.ForeignKey(Rack, db_column='rackid')
    sensor = models.ForeignKey(Sensor, db_column='sensorid')
    col = models.IntegerField()
    row = models.IntegerField()
    sensortype = VarcharField(blank=True)

    class Meta(object):
        db_table = 'racksensor'

    def __unicode__(self):
        return "Sensor {} in rack {}".format(self.sensor, self.rack)
