#
# Copyright (C) 2013 UNINETT
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
"""Sensors collection and logging to graphite"""

from twisted.internet import defer
import time
from nav.ipdevpoll import Plugin
from nav.ipdevpoll.db import autocommit, run_in_thread
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import metric_path_for_sensor
from nav.models.manage import Sensor

# Ask for no more than this number of values in a single SNMP GET operation
MAX_SENSORS_PER_REQUEST = 10


class StatSensors(Plugin):
    """Collects measurement values from registered sensors and pushes to
    Graphite.

    """
    @classmethod
    @defer.inlineCallbacks
    def can_handle(cls, netbox):
        base_can_handle = yield defer.maybeDeferred(
            super(StatSensors, cls).can_handle, netbox)
        if base_can_handle:
            i_can_handle = yield run_in_thread(cls._has_sensors, netbox)
            defer.returnValue(i_can_handle)
        defer.returnValue(base_can_handle)

    @classmethod
    @autocommit
    def _has_sensors(cls, netbox):
        return Sensor.objects.filter(netbox=netbox.id).count() > 0

    @defer.inlineCallbacks
    def handle(self):
        sensors = yield run_in_thread(self._get_sensors)
        self._logger.debug("retrieving data from %d sensors", len(sensors))
        oids = sensors.keys()
        requests = [oids[x:x+MAX_SENSORS_PER_REQUEST]
                    for x in range(0, len(oids), MAX_SENSORS_PER_REQUEST)]
        for req in requests:
            data = yield self.agent.get(req).addCallback(
                self._response_to_metrics, sensors)
            self._logger.debug("got data from sensors: %r", data)

    @autocommit
    def _get_sensors(self):
        sensors = Sensor.objects.filter(netbox=self.netbox.id).values()
        return dict((row['oid'], row) for row in sensors)

    def _response_to_metrics(self, result, sensors):
        metrics = []
        timestamp = time.time()
        data = ((sensors[oid], value) for oid, value in result.iteritems()
                if oid in sensors)
        for sensor, value in data:
            value = convert_to_precision(value, sensor)
            path = metric_path_for_sensor(self.netbox,
                                          sensor['internal_name'])
            metrics.append((path, (timestamp, value)))
        send_metrics(metrics)
        return metrics


def convert_to_precision(value, sensor):
    """Moves the decimal point of a value according to the precision defined
    for sensor

    """
    prec = sensor.get('precision', 0)
    return value * (10 ** -prec) if value and prec else value
