from unittest import TestCase
from mock import patch, Mock

from twisted.internet import defer
from twisted.internet.defer import succeed

from nav.mibs.juniper_dom_mib import JuniperDomMib, SENSOR_COLUMNS, THRESHOLD_COLUMNS


class TestJuniperDomMIB(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_handle_sensor_column_returns_correct_amount_of_sensor_dicts(self):
        rows_for_column = {"0": "interface 0", "1": "interface 1"}

        with patch(
            'nav.mibs.juniper_dom_mib.JuniperDomMib.retrieve_column'
        ) as retrieve:
            retrieve.return_value = succeed(rows_for_column)
            mib = JuniperDomMib(Mock())
            column = "jnxDomCurrentRxLaserPower"
            deferred_result = mib.handle_sensor_column(column, SENSOR_COLUMNS[column])
            result = deferred_result.result
        self.assertEqual(len(result), len(rows_for_column))

    def test_handle_threshold_column_returns_correct_amount_of_sensor_dicts(self):
        rows_for_column = {"0": "interface 0", "1": "interface 1"}

        with patch(
            'nav.mibs.juniper_dom_mib.JuniperDomMib.retrieve_column'
        ) as retrieve:
            retrieve.return_value = succeed(rows_for_column)
            mib = JuniperDomMib(Mock())
            threshold_column = "jnxDomCurrentRxLaserPowerHighAlarmThreshold"
            sensor_column = "jnxDomCurrentRxLaserPower"
            deferred_result = mib.handle_threshold_column(
                threshold_column,
                THRESHOLD_COLUMNS[sensor_column][threshold_column],
                sensor_column,
                SENSOR_COLUMNS[sensor_column],
            )
            result = deferred_result.result
        self.assertEqual(len(result), len(rows_for_column), result)
