"""A class for getting DDM values for ALE equipment
"""

from twisted.internet import defer
from twisted.internet.defer import returnValue
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor

COLUMNS = {
    "ddmPortTemperature": {
        "unit_of_measurement": Sensor.UNIT_CELSIUS,
        "precision": 3,
        "scale": Sensor.SCALE_MILLI,
        "name": "{ifc} Module Temperature",
        "description": "{ifc} Module Temperature",
    },
    "ddmPortTxBiasCurrent": {
        "unit_of_measurement": Sensor.UNIT_AMPERES,
        "precision": 3,
        "scale": Sensor.SCALE_MILLI,
        "name": "{ifc} TX Laser Bias Current",
        "description": "{ifc} TX Laser Bias Current",
    },
    "ddmPortTxOutputPower": {
        "unit_of_measurement": Sensor.UNIT_DBM,
        "precision": 3,
        "scale": Sensor.SCALE_MILLI,
        "name": "{ifc} TX Laser Output Power",
        "description": "{ifc} TX Laser Output Power",
    },
    "ddmPortRxOpticalPower": {
        "unit_of_measurement": Sensor.UNIT_DBM,
        "precision": 3,
        "scale": Sensor.SCALE_MILLI,
        "name": "{ifc} RX Laser Input Power",
        "description": "{ifc} RX Laser Input Power",
    }
}


class AlcatelInd1PortMib(MibRetriever):
    """MibRetriever for Alcatel Port Sensors"""
    from nav.smidumps.alcatel_ind1_port_mib import MIB as mib
    
    @defer.inlineCallbacks
    def get_all_sensors(self):
        """Discovers and returns all eligible dom sensors from this
        device.
        """
        sensors = []
        for column, config in COLUMNS.items():
            sensors += yield self.handle_column(column, config)
        returnValue(sensors)

    @defer.inlineCallbacks
    def handle_column(self, column, config):
        """Returns the sensors of the given type"""
        result = []
        value_oid = self.nodes[column].oid
        rows = yield self.retrieve_column(column)
        for row in rows:
            sensor = dict(
                oid=str(value_oid + row),
                scale=None,
                mib=self.get_module_name(),
                internal_name="{ifc}." + column,
                ifindex=row[-2],
            )
            print("SENSOR:")
            print(sensor)
            sensor.update(config)
            result.append(sensor)
        returnValue(result)
        
