# -*- coding: utf-8 -*-
#
# Copyright (C) 2007-2017 Uninett AS
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
"""Models for racks and rack items"""
import json
from itertools import chain

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from nav.models.fields import VarcharField
from nav.models.manage import Room, Sensor


class RackManager(models.Manager):
    """A manager for the rack model"""

    def get_all_sensor_pks_in_room(self, room):
        """Returns an exhaustive list of the primary keys of sensors added to
        all racks in the given room.

        :type room: nav.models.manage.Room

        """
        sensor_pks = (rack.get_all_sensor_pks()
                      for rack in self.filter(room=room))
        return set(chain(*sensor_pks))


@python_2_unicode_compatible
class Rack(models.Model):
    """A physical rack placed in a room."""

    objects = RackManager()

    id = models.AutoField(primary_key=True, db_column='rackid')
    room = models.ForeignKey(Room, db_column='roomid')
    rackname = VarcharField(blank=True)
    ordering = models.IntegerField()
    _configuration = VarcharField(default=None, db_column='configuration')
    __configuration = None
    item_counter = models.IntegerField(default=0, null=False,
                                       db_column='item_counter')

    class Meta(object):
        db_table = 'rack'

    def __str__(self):
        return "'{}' in {}".format(self.rackname or self.id, self.room.pk)

    @property
    def configuration(self):
        """Gets (and sets) the rackitem configuration for this rack

        The rack item configuration is stored as JSONB, and is returned as a
        dict by psycopg.
        """
        if self.__configuration is None:
            if self._configuration is None:
                self._configuration = {}
            self._configuration.setdefault('left', [])
            self._configuration.setdefault('center', [])
            self._configuration.setdefault('right', [])
            self._configuration['left'] = [rack_decoder(x) for x
                                           in self._configuration['left']]
            self._configuration['right'] = [rack_decoder(x) for x
                                            in self._configuration['right']]
            self._configuration['center'] = [rack_decoder(x) for x
                                             in self._configuration['center']]
            self.__configuration = self._configuration

        return self.__configuration

    def save(self, *args, **kwargs):
        self._configuration = json.dumps(self.configuration, cls=RackEncoder)
        return super(Rack, self).save(*args, **kwargs)

    def _column(self, column):
        return self.configuration[column]

    @property
    def left_column(self):
        """Gets all rackitems in the left column"""
        return self._column('left')

    @property
    def right_column(self):
        """Gets all rackitems in the right column"""
        return self._column('right')

    @property
    def center_column(self):
        """Gets all rackitems in the center column"""
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
    """Instantiates the correct object based on __type__ internal"""
    if '__type__' in obj:
        if obj['__type__'] == 'SensorRackItem':
            return SensorRackItem(**obj)
        if obj['__type__'] == 'SensorsDiffRackItem':
            return SensorsDiffRackItem(**obj)
        if obj['__type__'] == 'SensorsSumRackItem':
            return SensorsSumRackItem(**obj)
    return obj


class RackEncoder(json.JSONEncoder):
    """TODO: Write doc"""
    def default(self, obj):
        if isinstance(obj, BaseRackItem):
            return obj.to_json()
        # Let the base class default method raise the TypeError
        return json.JSONEncoder.default(self, obj)


class BaseRackItem(object):
    """The super class for rack items

    This class should never be used directly
    """

    def __init__(self, id=None, **kwargs):
        self.id = id

    def to_json(self):
        """TODO: Not really to_json is it?"""
        return {
            '__type__': self.__class__.__name__,
            'id': self.id,
        }

    def title(self):
        """A possible long description"""
        return self.human_readable

    def get_metric(self):
        """Returns the metric used for getting the values"""
        raise NotImplementedError

    def unit_of_measurement(self):
        """Returns the unit of measurement

        :rtype: str
        """
        raise NotImplementedError

    def get_absolute_url(self):
        """Returns the linktarget"""
        pass

    def human_readable(self):
        """A short and consise description"""
        raise NotImplementedError

    def get_display_range(self):
        """Gets the range of values for this sensor

        Is a list to simplify front-end usage
        """
        raise NotImplementedError


class SensorRackItem(BaseRackItem):
    """A rackitem that display the value of a sensor"""

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
        data['sensor'] = self.sensor.pk if self.sensor_exists() else self.sensor
        return data

    def title(self):
        if self.sensor_exists():
            return str(self.sensor)
        else:
            return "Sensor {} no longer exists".format(self.sensor)

    def get_metric(self):
        if self.sensor_exists():
            return self.sensor.get_metric_name()

    def unit_of_measurement(self):
        if self.sensor_exists():
            return self.sensor.unit_of_measurement

    def get_absolute_url(self):
        if self.sensor_exists():
            return self.sensor.get_absolute_url()

    def human_readable(self):
        if self.sensor_exists():
            return self.sensor.human_readable

    def get_display_range(self):
        if self.sensor_exists():
            return list(self.sensor.get_display_range())
        else:
            return []

    def sensor_exists(self):
        return isinstance(self.sensor, Sensor)


class SensorsDiffRackItem(BaseRackItem):
    """A rackitem that display the difference of two sensors"""

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

    def get_display_range(self):
        return list(self.minuend.get_display_range())


class SensorsSumRackItem(BaseRackItem):
    """A rackitem that display the sum of several sensors"""

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
        if self.sensors:
            return self.sensors[0].unit_of_measurement
        return 'N/A'

    def get_absolute_url(self):
        return ""

    def human_readable(self):
        return self._title

    def get_display_range(self):
        return [sum(r) for r in
                zip(*[s.get_display_range()
                      for s in self.sensors])]
