import pytest

from nav.models.manage import Sensor
from nav.models.rack import Rack, SensorRackItem


class TestRack:
    def test_that_rack_configuration_can_be_saved_without_error(self, test_rack):
        test_rack.save()
        assert test_rack.id

    def test_that_rack_configuration_is_a_dict(self, test_rack):
        test_rack.save()
        rack = Rack.objects.get(id=test_rack.id)
        print(repr(Rack._configuration))
        assert isinstance(rack._configuration, dict)

    def test_that_rack_configuration_can_be_loaded_without_error(self, test_rack):
        test_rack.save()
        rack = Rack.objects.get(id=test_rack.id)
        assert rack.configuration


@pytest.fixture
def test_rack(test_sensor):
    rack = Rack(room=test_sensor.netbox.room, rackname="Rack 1")
    item = SensorRackItem(test_sensor)
    rack.add_left_item(item)
    return rack


@pytest.fixture
def test_sensor(localhost):
    sensor = Sensor(
        netbox=localhost, oid="1.2.3", unit_of_measurement=Sensor.UNIT_CELSIUS
    )
    sensor.save()
    yield sensor
    sensor.delete()
