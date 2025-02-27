from twisted.internet import defer
from twisted.internet.defer import returnValue

from nav.smidumps import get_mib
from nav.mibs import mibretriever, reduce_index
from nav.models.manage import Sensor


DEGREES_CELSIUS = "\xb0C"
DEGREES_FAHRENHEIT = "\xb0F"
UNIT_MAP = {
    DEGREES_CELSIUS: Sensor.UNIT_CELSIUS,
    DEGREES_FAHRENHEIT: Sensor.UNIT_FAHRENHEIT,
}


class T3611Mib(mibretriever.MibRetriever):
    mib = get_mib("T3611-MIB")

    @defer.inlineCallbacks
    def get_all_sensors(self):
        result = (
            yield self.retrieve_columns(
                ["temp", "hum", "tempUnit", "humUnit", "sensorName"]
            )
            .addCallback(self.translate_result)
            .addCallback(reduce_index)
        )

        returnValue(self._data_to_sensor(result))

    def _data_to_sensor(self, result):
        temp_internal_name = "temperature %s" % result[0]["sensorName"]
        temp_name = "temperature"
        temp_unit = UNIT_MAP[result.get("tempUnit", DEGREES_CELSIUS)]
        temp_mibobject = self.nodes.get("temp")
        temp_readout_oid = str(temp_mibobject.oid + str(0))

        hum_internal_name = "humidity %s" % result[0]["sensorName"]
        hum_name = "humidity"
        hum_mibobject = self.nodes.get("hum")
        hum_readout_oid = str(hum_mibobject.oid + str(0))

        returnValue(
            [
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
        )
