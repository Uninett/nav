from nav.models.manage import Sensor


def test_sensor_normalized_units_should_accept_blank_units():
    """Some sensors just count things that have no unit of measurement"""
    sensor = Sensor(unit_of_measurement=None)
    assert sensor.normalized_unit == ""
