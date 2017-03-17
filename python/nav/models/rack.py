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
        return set(chain(*sensor_pks))


class Rack(models.Model):
    """A physical rack placed in a room."""

    objects = RackManager()

    id = models.AutoField(primary_key=True, db_column='rackid')
    room = models.ForeignKey(Room, db_column='roomid')
    rackname = VarcharField(blank=True)
    ordering = models.IntegerField()
    _configuration = VarcharField(default='{}', db_column='configuration')
    __configuration = None
    item_counter = models.IntegerField(default=0, null=False,
                                       db_column='item_counter')

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
            self.configuration.setdefault('left', [])
            self.configuration.setdefault('center', [])
            self.configuration.setdefault('right', [])
        return self.__configuration

    def save(self, *args, **kwargs):
        self._configuration = json.dumps(self.configuration, cls=RackEncoder)
        return super(Rack, self).save(*args, **kwargs)

    def _column(self, column):
        return self.configuration[column]

    @property
    def left_column(self):
        return self._column('left')

    @property
    def right_column(self):
        return self._column('right')

    @property
    def center_column(self):
        return self._column('center')

    def add_left_item(self, item):
        """
        :type item: RackItem
        """
        self.item_counter += 1
        item.id = self.item_counter
        self.left_column.append(item)

    def add_center_item(self, item):
        """
        :type item: RackItem
        """
        self.item_counter += 1
        item.id = self.item_counter
        self.center_column.append(item)

    def add_right_item(self, item):
        """
        :type item: RackItem
        """
        self.item_counter += 1
        item.id = self.item_counter
        self.right_column.append(item)

    def remove_left_item(self, index):
        """
        :type index: int
        """
        self.left_column.pop(index)

    def remove_center_item(self, index):
        """
        :type index: int
        """
        self.center_column.pop(index)

    def remove_right_item(self, index):
        """
        :type index: int
        """
        self.right_column.pop(index)

    def get_all_sensor_pks(self):
        """Returns an exhaustive list of the primary keys of sensors in this
        rack
        """
        return []


def rack_decoder(obj):
    if '__type__' in obj:
        if obj['__type__'] == 'SensorRackItem':
            return SensorRackItem(**obj)
        if obj['__type__'] == 'SensorsDiffRackItem':
            return SensorsDiffRackItem(**obj)
        if obj['__type__'] == 'SensorsSumRackItem':
            return SensorsSumRackItem(**obj)
    return obj


class RackEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseRackItem):
            return obj.to_json()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class BaseRackItem(object):
    def __init__(self, id=None, **kwargs):
        self.id = id

    def to_json(self):
        return {
            '__type__': self.__class__.__name__,
            'id': self.id,
        }

    def title(self):
        return "Title"

    def get_metric(self):
        return ""

    def unit_of_measurement(self):
        return "SI"

    def get_absolute_url(self):
        return "https://example.com"

    def human_readable(self):
        return "A proper description"


class SensorRackItem(BaseRackItem):
    def __init__(self, sensor, **kwargs):
        super(SensorRackItem, self).__init__(**kwargs)
        self.sensor = sensor
        if isinstance(sensor, int):
            try:
                self.sensor = Sensor.objects.get(pk=sensor)
            except Sensor.DoesNotExist:
                pass

    def to_json(self):
        data = super(SensorRackItem, self).to_json()
        data['sensor'] = self.sensor.pk
        return data

    def title(self):
        return str(self.sensor)

    def get_metric(self):
        return self.sensor.get_metric_name()

    def unit_of_measurement(self):
        return self.sensor.unit_of_measurement

    def get_absolute_url(self):
        return self.sensor.netbox.get_absolute_url()

    def human_readable(self):
        return self.sensor.human_readable


class SensorsDiffRackItem(BaseRackItem):
    def __init__(self, minuend, subtrahend, **kwargs):
        super(SensorsDiffRackItem, self).__init__(**kwargs)
        self.minuend = minuend
        self.subtrahend = subtrahend
        if isinstance(minuend, int):
            try:
                self.minuend = Sensor.objects.get(pk=minuend)
            except Sensor.DoesNotExist:
                pass
        if isinstance(subtrahend, int):
            try:
                self.subtrahend = Sensor.objects.get(pk=subtrahend)
            except Sensor.DoesNotExist:
                pass

    def to_json(self):
        data = super(SensorsDiffRackItem, self).to_json()
        data['minuend'] = self.minuend.pk
        data['subtrahend'] = self.subtrahend.pk
        return data

    def title(self):
        return "Difference between {} and {}".format(self.minuend,
                                                     self.subtrahend)

    def get_metric(self):
        return "diffSeries({minuend},{subtrahend})".format(
            minuend=self.minuend.get_metric_name(),
            subtrahend=self.subtrahend.get_metric_name()
        )

    def unit_of_measurement(self):
        return self.minuend.unit_of_measurement

    def get_absolute_url(self):
        return ""

    def human_readable(self):
        return "{} - {}".format(self.minuend.human_readable,
                                self.subtrahend.human_readable)


class SensorsSumRackItem(BaseRackItem):
    def __init__(self, title, sensors, **kwargs):
        super(SensorsSumRackItem, self).__init__(**kwargs)
        self.sensors = sensors
        self._title = title
        for i, sensor in enumerate(self.sensors):
            if isinstance(sensor, int):
                try:
                    self.sensors[i] = Sensor.objects.get(pk=sensor)
                except Sensor.DoesNotExist:
                    pass

    def to_json(self):
        data = super(SensorsSumRackItem, self).to_json()
        data['sensors'] = [sensor.pk for sensor in self.sensors]
        data['title'] = self._title
        return data

    def title(self):
        return ", ".join([s.human_readable for s in self.sensors])

    def get_metric(self):
        return "sumSeries({})".format(
            ",".join((s.get_metric_name() for s in self.sensors))
        )

    def unit_of_measurement(self):
        return self.sensors[0].unit_of_measurement

    def get_absolute_url(self):
        return ""

    def human_readable(self):
        return self._title
