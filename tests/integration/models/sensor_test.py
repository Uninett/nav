from nav.models.manage import Sensor
import pytest


class TestSensor:
    def test_threshold_for_property_returns_the_sensor_the_current_sensor_is_a_threshold_for(
        self, db, sensor, threshold_sensor1
    ):
        threshold_for_sensor = threshold_sensor1.threshold_for
        assert True == False
        assert threshold_for_sensor == sensor

    def test_thresholds_property_returns_all_sensors_that_are_thresholds_for_current_sensor(
        self, db, sensor, threshold_sensor1, threshold_sensor2
    ):
        threshold_sensors = sensor.thresholds
        assert True == False
        assert set(threshold_sensors) == set([threshold_sensor1, threshold_sensor2])


@pytest.fixture
def threshold_sensor1(db, localhost):
    sensor = Sensor(
        netbox=localhost,
        oid="1.2.4",
        unit_of_measurement=Sensor.UNIT_OTHER,
        data_scale=Sensor.SCALE_MILLI,
        precision=1,
        human_readable="threshold_sensor1",
        name="threshold_sensor1",
        internal_name="threshold_sensor1",
        mib="testmib",
        threshold_for_oid="1.2.3",
    )
    sensor.save()
    yield sensor
    if sensor.pk:
        sensor.delete()


@pytest.fixture
def threshold_sensor2(db, localhost):
    sensor = Sensor(
        netbox=localhost,
        oid="1.2.5",
        unit_of_measurement=Sensor.UNIT_OTHER,
        data_scale=Sensor.SCALE_MILLI,
        precision=1,
        human_readable="threshold_sensor2",
        name="threshold_sensor2",
        internal_name="threshold_sensor2",
        mib="testmib",
        threshold_for_oid="1.2.3",
    )
    sensor.save()
    yield sensor
    if sensor.pk:
        sensor.delete()


@pytest.fixture
def sensor(db, localhost):
    sensor = Sensor(
        netbox=localhost,
        oid="1.2.3",
        unit_of_measurement=Sensor.UNIT_OTHER,
        data_scale=Sensor.SCALE_MILLI,
        precision=1,
        human_readable="value",
        name="sensor",
        internal_name="sensor",
        mib="testmib",
    )
    sensor.save()
    yield sensor
    if sensor.pk:
        sensor.delete()
