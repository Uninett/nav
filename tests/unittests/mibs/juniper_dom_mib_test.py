import pytest
from mock import patch, Mock

from twisted.internet.defer import succeed

from nav.mibs.juniper_dom_mib import JuniperDomMib, SENSOR_COLUMNS, THRESHOLD_COLUMNS
from nav.models.manage import Sensor


class TestHandleSensorColumn:
    def test_when_a_column_has_rows_then_each_row_should_yield_one_sensor(self):
        column = "jnxDomCurrentRxLaserPower"
        rows = {(1,): "interface 1", (2,): "interface 2"}

        sensors = _run_handle_sensor_column(column, rows)

        assert len(sensors) == len(rows)

    def test_when_handling_a_column_then_oid_and_ifindex_should_derive_from_the_row(
        self,
    ):
        column = "jnxDomCurrentRxLaserPower"
        rows = {(1,): "interface 1", (2,): "interface 2"}

        sensors = _run_handle_sensor_column(column, rows)

        value_oid = JuniperDomMib(Mock()).nodes[column].oid
        by_ifindex = {sensor["ifindex"]: sensor for sensor in sensors}
        assert set(by_ifindex) == {1, 2}
        for suffix in rows:
            assert by_ifindex[suffix[-1]]["oid"] == str(value_oid + suffix)


class TestHandleThresholdColumn:
    @pytest.mark.parametrize(
        "threshold_column, expected_threshold_type, expected_alert_type",
        [
            (
                "jnxDomCurrentRxLaserPowerHighAlarmThreshold",
                Sensor.THRESHOLD_TYPE_HIGH,
                Sensor.ALERT_TYPE_ALERT,
            ),
            (
                "jnxDomCurrentRxLaserPowerLowAlarmThreshold",
                Sensor.THRESHOLD_TYPE_LOW,
                Sensor.ALERT_TYPE_ALERT,
            ),
            (
                "jnxDomCurrentRxLaserPowerHighWarningThreshold",
                Sensor.THRESHOLD_TYPE_HIGH,
                Sensor.ALERT_TYPE_WARNING,
            ),
            (
                "jnxDomCurrentRxLaserPowerLowWarningThreshold",
                Sensor.THRESHOLD_TYPE_LOW,
                Sensor.ALERT_TYPE_WARNING,
            ),
        ],
    )
    def test_when_handling_a_threshold_column_then_each_sensor_should_carry_matching_metadata(  # noqa: E501
        self, threshold_column, expected_threshold_type, expected_alert_type
    ):
        sensor_column = "jnxDomCurrentRxLaserPower"
        rows = {(1,): "interface 1", (2,): "interface 2"}

        thresholds = _run_handle_threshold_column(threshold_column, sensor_column, rows)

        assert len(thresholds) == len(rows)
        for threshold in thresholds:
            assert threshold["threshold_type"] == expected_threshold_type
            assert threshold["threshold_alert_type"] == expected_alert_type
            # a threshold inherits unit/precision from the sensor it guards;
            # jnxDomCurrentRxLaserPower is dBm with 2 decimals of precision
            assert threshold["unit_of_measurement"] == Sensor.UNIT_DBM
            assert threshold["precision"] == 2

    def test_when_handling_a_threshold_column_then_threshold_for_oid_should_match_parent_oid(  # noqa: E501
        self,
    ):
        sensor_column = "jnxDomCurrentRxLaserPower"
        threshold_column = "jnxDomCurrentRxLaserPowerHighAlarmThreshold"
        rows = {(1,): "interface 1", (2,): "interface 2"}

        parent_sensors = _run_handle_sensor_column(sensor_column, rows)
        thresholds = _run_handle_threshold_column(threshold_column, sensor_column, rows)

        parent_oid_by_ifindex = {s["ifindex"]: s["oid"] for s in parent_sensors}
        assert thresholds  # guard against a vacuous pass
        for threshold in thresholds:
            assert (
                threshold["threshold_for_oid"]
                == parent_oid_by_ifindex[threshold["ifindex"]]
            )


def _run_handle_sensor_column(column, rows):
    with patch('nav.mibs.juniper_dom_mib.JuniperDomMib.retrieve_column') as retrieve:
        retrieve.return_value = succeed(rows)
        mib = JuniperDomMib(Mock())
        return mib.handle_sensor_column(column, SENSOR_COLUMNS[column]).result


def _run_handle_threshold_column(threshold_column, sensor_column, rows):
    with patch('nav.mibs.juniper_dom_mib.JuniperDomMib.retrieve_column') as retrieve:
        retrieve.return_value = succeed(rows)
        mib = JuniperDomMib(Mock())
        return mib.handle_threshold_column(
            threshold_column,
            THRESHOLD_COLUMNS[sensor_column][threshold_column],
            sensor_column,
            SENSOR_COLUMNS[sensor_column],
        ).result
