from unittest import TestCase
from nav.mibs.entity_mib import EntityTable


class TestEntityMIB(TestCase):
    def setUp(self):
        self.entity_table = EntityTable(
            {
                1: {
                    'entPhysicalDescr': 'Transceiver Port',
                    'entPhysicalContainedIn': 0,
                    'entPhysicalClass': 'port',
                    'entPhysicalSerialNum': '',
                    'entPhysicalIsFRU': False,
                    0: 1,
                },
                2: {
                    'entPhysicalDescr': 'Transceiver Port Container',
                    'entPhysicalContainedIn': 1,
                    'entPhysicalClass': 'container',
                    'entPhysicalSerialNum': '',
                    'entPhysicalIsFRU': False,
                    0: 2,
                },
            }
        )

    def test_module_is_module(self):
        module = {
            'entPhysicalDescr': 'Chassis',
            'entPhysicalContainedIn': 1,
            'entPhysicalClass': 'module',
            'entPhysicalSerialNum': '1',
            'entPhysicalIsFRU': True,
        }

        self.assertTrue(EntityTable.is_module(self.entity_table, module))

    def test_transceiver_is_not_module(self):
        transceiver = {
            'entPhysicalDescr': 'Transceiver',
            'entPhysicalContainedIn': 2,
            'entPhysicalClass': 'module',
            'entPhysicalSerialNum': '1',
            'entPhysicalIsFRU': True,
        }

        self.assertFalse(EntityTable.is_module(self.entity_table, transceiver))

    def test_sensor_is_not_module(self):
        sensor = {
            'entPhysicalDescr': 'Sensor',
            'entPhysicalContainedIn': 1,
            'entPhysicalClass': 'sensor',
            'entPhysicalSerialNum': '',
            'entPhysicalIsFRU': False,
        }

        self.assertFalse(EntityTable.is_module(self.entity_table, sensor))

    def test_not_FRU_is_not_module(self):
        sensor = {
            'entPhysicalDescr': 'Chassis',
            'entPhysicalContainedIn': 1,
            'entPhysicalClass': 'module',
            'entPhysicalSerialNum': '1',
            'entPhysicalIsFRU': False,
        }

        self.assertFalse(EntityTable.is_module(self.entity_table, sensor))

    def test_entity_without_serial_number_is_not_module(self):
        sensor = {
            'entPhysicalDescr': 'Chassis',
            'entPhysicalContainedIn': 1,
            'entPhysicalClass': 'module',
            'entPhysicalSerialNum': '',
            'entPhysicalIsFRU': True,
        }

        self.assertFalse(EntityTable.is_module(self.entity_table, sensor))
