#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Sensors collection and logging to graphite"""

import time

from twisted.internet import defer

from nav.Snmp import safestring
from nav.ipdevpoll import Plugin
from nav.ipdevpoll import db
from nav.ipdevpoll.db import run_in_thread
from nav.metrics.carbon import send_metrics
from nav.metrics.templates import metric_path_for_sensor
from nav.models.manage import Sensor

# Ask for no more than this number of values in a single SNMP GET operation
MAX_SENSORS_PER_REQUEST = 5


class StatSensors(Plugin):
    """Collects measurement values from registered sensors and pushes to
    Graphite.

    """

    @classmethod
    @defer.inlineCallbacks
    def can_handle(cls, netbox):
        base_can_handle = yield defer.maybeDeferred(
            super(StatSensors, cls).can_handle, netbox
        )
        if base_can_handle:
            i_can_handle = yield run_in_thread(cls._has_sensors, netbox)
            return i_can_handle
        return base_can_handle

    @classmethod
    def _has_sensors(cls, netbox):
        return Sensor.objects.filter(netbox=netbox.id).count() > 0

    @defer.inlineCallbacks
    def handle(self):
        if self.netbox.master:
            return None
        netboxes = yield db.run_in_thread(self._get_netbox_list)
        sensors = yield run_in_thread(self._get_sensors)
        self._logger.debug("retrieving data from %d sensors", len(sensors))
        oids = list(sensors.keys())
        requests = [
            oids[x : x + MAX_SENSORS_PER_REQUEST]
            for x in range(0, len(oids), MAX_SENSORS_PER_REQUEST)
        ]
        for req in requests:
            data = yield self.agent.get(req).addCallback(
                self._response_to_metrics, sensors, netboxes
            )
            self._logger.debug("got data from sensors: %r", data)

    def _get_sensors(self):
        sensors = Sensor.objects.filter(netbox=self.netbox.id).values()
        return dict((row['oid'], row) for row in sensors)

    def _response_to_metrics(self, result, sensors, netboxes):
        metrics = []
        timestamp = time.time()
        data = (
            (sensors[oid], value) for oid, value in result.items() if oid in sensors
        )
        for sensor, value in data:
            # Attempt to support numbers-as-text values
            if isinstance(value, bytes):
                value = safestring(value)
            if isinstance(value, str):
                try:
                    value = float(value)
                except ValueError:
                    pass

            value = convert_to_precision(value, sensor)
            for netbox in netboxes:
                path = metric_path_for_sensor(netbox, sensor['internal_name'])
                metrics.append((path, (timestamp, value)))
        send_metrics(metrics)
        return metrics


def convert_to_precision(value, sensor):
    """Moves the decimal point of a value according to the precision defined
    for sensor

    """
    prec = sensor.get('precision', 0)
    return value * (10**-prec) if value and prec else value
