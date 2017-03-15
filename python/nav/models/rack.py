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
import json
from itertools import chain

from django.db import models

from nav.models.fields import VarcharField
from nav.models.manage import Room, Sensor


class RackManager(models.Manager):
    def get_all_sensor_pks_in_room(self, room):
        """Returns an exhaustive list of the primary keys of sensors added to
        all racks in the given room.

        :type room: nav.models.manage.Room

        """
        sensor_pks = (rack.get_all_sensor_pks()
                      for rack in self.filter(room=room))
        return set(*chain(sensor_pks))


class Rack(models.Model):
    """A physical rack placed in a room."""

    objects = RackManager()

    id = models.AutoField(primary_key=True, db_column='rackid')
    room = models.ForeignKey(Room, db_column='roomid')
    rackname = VarcharField(blank=True)
    ordering = models.IntegerField()
    _configuration = VarcharField(default='{}', db_column='configuration')
    __configuration = None

    class Meta(object):
        db_table = 'rack'

    def __unicode__(self):
        return "Rack %r in %r" % (self.rackname or self.id, self.room)

    @property
    def configuration(self):
        if self.__configuration is None:
            self.__configuration = json.loads(self._configuration,
                                              object_hook=rack_decoder)
            if self.__configuration is None:
                self.__configuration = {}
        return self.__configuration

    def save(self, *args, **kwargs):
        self._configuration = json.dumps(self.__configuration, cls=RackEncoder)
        return super(Rack, self).save(*args, **kwargs)

    def add_left_item(self, item):
        """
        :type item: RackItem
        """
        self.configuration.setdefault('left', []).append(item)

    def add_center_item(self, item):
        """
        :type item: RackItem
        """
        self.configuration.setdefault('center', []).append(item)

    def add_right_item(self, item):
        """
        :type item: RackItem
        """
        self.configuration.setdefault('right', []).append(item)

    def get_all_sensor_pks(self):
        """Returns an exhaustive list of the primary keys of sensors in this
        rack
        """
        return []


def rack_decoder(obj):
    if '__type__' in obj:
        if obj['__type__'] == 'RackItem':
            return RackItem(obj['sensor'])
    return obj


class RackEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, RackItem):
            return {'__type__': 'RackItem',
                    'sensor': getattr(obj.sensor, 'pk', obj.sensor)
                    }
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class RackItem(object):
    def __init__(self, sensor=None):
        self.sensor = sensor
        if isinstance(sensor, int):
            try:
                self.sensor = Sensor.objects.get(pk=sensor)
            except Sensor.DoesNotExist:
                pass
