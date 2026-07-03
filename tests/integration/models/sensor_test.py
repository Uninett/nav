import pytest

from nav.models.manage import Sensor


class TestThresholdFor:
    def test_when_sensor_is_a_threshold_then_threshold_for_should_return_its_parent(
        self, db, sensor, threshold_sensor1
    ):
        assert threshold_sensor1.threshold_for == sensor


class TestThresholds:
    def test_when_sensor_has_thresholds_then_thresholds_should_return_exactly_them(
        self, db, sensor, threshold_sensor1, threshold_sensor2
    ):
        assert set(sensor.thresholds.all()) == {threshold_sensor1, threshold_sensor2}

    def test_when_sensor_has_no_thresholds_then_thresholds_should_be_empty(
        self, db, threshold_sensor1
    ):
        assert list(threshold_sensor1.thresholds.all()) == []


@pytest.fixture
def sensor(db, localhost):
    return _make_sensor(localhost, oid="1.2.3", name="sensor")


@pytest.fixture
def threshold_sensor1(db, localhost, sensor):
    return _make_sensor(
        localhost, oid="1.2.4", name="threshold_sensor1", threshold_for=sensor
    )


@pytest.fixture
def threshold_sensor2(db, localhost, sensor):
    return _make_sensor(
        localhost, oid="1.2.5", name="threshold_sensor2", threshold_for=sensor
    )


def _make_sensor(netbox, oid, name, threshold_for=None):
    sensor = Sensor(
        netbox=netbox,
        oid=oid,
        unit_of_measurement=Sensor.UNIT_OTHER,
        data_scale=Sensor.SCALE_MILLI,
        precision=1,
        human_readable=name,
        name=name,
        internal_name=name,
        mib="testmib",
        threshold_for=threshold_for,
    )
    sensor.save()
    return sensor
