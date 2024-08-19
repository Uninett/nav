#
# Copyright (C) 2025 University of Tromsø and Heimonen Solutions
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

"""A class for retrieving temperature and humidity data from a Comet T3611"""

from twisted.internet import defer

from nav.smidumps import get_mib
from nav.mibs import mibretriever, reduce_index
from nav.models.manage import Sensor

from nav.mibs.comet import UNIT_MAP, DEGREES_CELSIUS


class CometT3611(mibretriever.MibRetriever):
    """MibRetriever for the Comet T3611"""

    mib = get_mib("T3611-MIB")

    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Fetches temperature and humidity sensors from the Comet T3611 MIB."""
        result = (
            yield self.retrieve_columns(
                ["temp", "hum", "tempUnit", "humUnit", "sensorName"]
            )
            .addCallback(self.translate_result)
            .addCallback(reduce_index)
        )

        return self._data_to_sensor(result)

    def _data_to_sensor(self, result):
        """Processes MIB data and returns a humidity and temperature sensor pair"""
        temp_internal_name = "temperature %s" % result[0]["sensorName"]
        temp_name = "temperature"
        temp_unit = UNIT_MAP[result.get("tempUnit", DEGREES_CELSIUS)]
        temp_mibobject = self.nodes.get("temp")
        temp_readout_oid = str(temp_mibobject.oid + str(0))

        hum_internal_name = "humidity %s" % result[0]["sensorName"]
        hum_name = "humidity"
        hum_mibobject = self.nodes.get("hum")
        hum_readout_oid = str(hum_mibobject.oid + str(0))

        return [
            dict(
                oid=temp_readout_oid,
                unit_of_measurement=temp_unit,
                precision=0,
                scale=None,
                description=temp_name,
                name=temp_name,
                internal_name=temp_internal_name,
                mib="T3611-MIB",
            ),
            dict(
                oid=hum_readout_oid,
                unit_of_measurement=Sensor.UNIT_PERCENT_RELATIVE_HUMIDITY,
                precision=0,
                scale=None,
                description=hum_name,
                name=hum_name,
                internal_name=hum_internal_name,
                mib="T3611-MIB",
            ),
        ]
