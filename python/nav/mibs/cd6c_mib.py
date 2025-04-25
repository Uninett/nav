from twisted.internet import defer
from nav.smidumps import get_mib
from nav.mibs.mibretriever import MibRetriever
from nav.models.manage import Sensor


class CD6CMib(MibRetriever):
    mib = get_mib('CD6C')
    sensors = {
        'uptime': 'cduStatusUpTime',  # Number of minutes since CDU power-up
        'temp': [
            ('cduStatusPrimaryTempT1', 'Primary temperature (T1) sensor value.'),
            ('cduStatusSecondaryTempT2a', 'Secondary temperature (T2a) sensor value.'),
            ('cduStatusSecondaryTempT2b', 'Secondary temperature (T2b) sensor value.'),
            (
                'cduStatusSecondaryReturnTempT4',
                'Secondary return temperature (T3) sensor value.',
            ),
        ],
        'pressure': [
            ('cduStatusPS1', 'Secondary Pressure PS1 sensor value.'),
            ('cduStatusPS2', 'Secondary Pressure PS2 sensor value.'),
            ('cduStatusPS3', 'Filter Inlet Pressure (PS3) sensor value.'),
            ('cduStatusPS4', 'Filter Outlet Pressure (PS4) sensor value.'),
        ],
        'flow': [
            ('cduStatusPrimaryFlowRate', 'Primary Chilled Water Flow Rate'),
            ('cduStatusSecondaryFlowRate', 'Secondary Flow Rate'),
        ],
    }

    @defer.inlineCallbacks
    def get_all_sensors(self):
        supported = yield self.get_next('main')
        if not supported:
            self._logger.debug('CD6C mib not supported - returned %s', supported)
            return []

        self._logger.debug('CD6C mib supported because main returned %s', supported)

        temp_sensors = [
            self.create_sensor(s, precision=1, uom=Sensor.UNIT_CELSIUS)
            for s in self.sensors['temp']
        ]
        pressure_sensors = [
            self.create_sensor(s, precision=2, uom=Sensor.UNIT_BAR)
            for s in self.sensors['pressure']
        ]
        flow_sensors = [
            self.create_sensor(s, uom=Sensor.UNIT_LPM) for s in self.sensors['flow']
        ]

        all_sensors = temp_sensors + pressure_sensors + flow_sensors

        return all_sensors

    def create_sensor(self, sensor, precision=0, uom=''):
        """Creates sensor object based on name"""
        name, descr = sensor

        return {
            'oid': self.mib['nodes'][name]['oid'] + '.0',
            'unit_of_measurement': uom,
            'precision': precision,
            'scale': None,
            'description': descr,
            'name': name,
            'internal_name': name,
            'mib': 'CD6C-MIB',
        }
