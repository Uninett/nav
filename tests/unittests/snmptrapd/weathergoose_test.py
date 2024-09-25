from mock import patch, Mock
import pytest

from nav.snmptrapd.handlers import weathergoose as wg


class TestWeatherGoose1Class(object):
    def test_should_not_handle_a_weathergoose2_trap(self):
        assert not (wg.WeatherGoose1.can_handle('.1.3.6.1.4.1.17373.3.32767.0.10205'))

    def test_should_handle_a_weathergoose1_trap(self):
        assert wg.WeatherGoose1.can_handle('.1.3.6.1.4.1.17373.0.10205')

    def test_should_map_oid_to_correct_trigger(self):
        assert (
            wg.WeatherGoose1.map_oid_to_trigger('.1.3.6.1.4.1.17373.0.10205')
            == 'cmClimateTempCTRAP'
        )

    def test_init_should_raise_on_invalid_oid(self):
        trap = Mock(snmpTrapOID='5')
        with pytest.raises(Exception):
            wg.WeatherGoose1(trap, None, None, None)


class Event(dict):
    def post(self):
        pass


@patch('nav.event.Event', new=Mock(side_effect=Event))
class TestWeatherGoose1Trap(object):
    trap = Mock(snmpTrapOID='.1.3.6.1.4.1.17373.0.10205')
    TRIP_TYPE_HIGH = 2
    goosename = 'cleese'
    temperature = 32
    trap.varbinds = {
        '.1.3.6.1.4.1.17373.2.1.6': TRIP_TYPE_HIGH,
        '.1.3.6.1.4.1.17373.2.2.1.3.1': goosename,
        '.1.3.6.1.4.1.17373.2.2.1.5.1': temperature,
    }

    def test_init_should_parse_trap_without_error(self):
        assert wg.WeatherGoose1(self.trap, None, None, None)

    def test_should_find_correct_alert_type(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        assert goose._get_alert_type() == 'cmClimateTempCTRAP'

    def test_should_find_correct_goosename(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        assert goose.goosename == self.goosename

    def test_should_find_climate_values(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        assert goose.climatevalue == self.temperature

    def test_should_find_triptype_high(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        assert goose.triptype == 'High'

    def test_event_event_post(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        assert goose.post_event()

    def test_should_find_correct_sensorname(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        assert goose._get_sensorname() == 'cleese'


class TestWeatherGoose2(object):
    def test_should_not_handle_a_weathergoose1_trap(self):
        assert not (wg.WeatherGoose2.can_handle('.1.3.6.1.4.1.17373.0.10205'))

    def test_should_handle_a_weathergoose2_trap(self):
        assert wg.WeatherGoose2.can_handle('.1.3.6.1.4.1.17373.3.32767.0.10205')

    def test_should_handle_a_weathergoose2_remote_trap(self):
        assert wg.WeatherGoose2.can_handle('.1.3.6.1.4.1.17373.3.32767.0.10405')

    def test_should_map_oid_to_correct_trigger(self):
        assert (
            wg.WeatherGoose2.map_oid_to_trigger('.1.3.6.1.4.1.17373.3.32767.0.10205')
            == 'cmClimateTempCNOTIFY'
        )

    def test_should_map_oid_to_correct_trigger_for_remote(self):
        assert (
            wg.WeatherGoose2.map_oid_to_trigger('.1.3.6.1.4.1.17373.3.32767.0.10405')
            == 'cmTempSensorTempCNOTIFY'
        )

    def test_should_find_correct_alert_type(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {'.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH}
        goose = wg.WeatherGoose2(trap, None, None, None)
        assert goose._get_alert_type() == 'cmClimateTempCNOTIFY'

    def test_should_find_correct_alert_type_remote(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10405'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {'.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH}
        goose = wg.WeatherGoose2(trap, None, None, None)
        assert goose._get_alert_type() == 'cmTempSensorTempCNOTIFY'

    def test_should_add_subid_when_alarminstance_defined(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
            '.1.3.6.1.4.1.17373.3.1.12.0': 4,
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        assert goose._get_subid() == 4

    def test_should_not_add_subid_when_not_in_varbinds(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        assert goose._get_subid() is None

    def test_should_find_correct_value_from_external_trap(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10405'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
            '.1.3.6.1.4.1.17373.3.4.1.5.1': 16,
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        assert goose._get_trigger_values()[0] == 16

    def test_should_find_correct_internal_sensorname(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.3.0': 'SuperGoose II',
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
            '.1.3.6.1.4.1.17373.3.2.1.3.1': 'SuperDuperGoose II',
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        assert goose._get_sensorname() == 'SuperDuperGoose II'
        assert goose.goosename == 'SuperGoose II'

    def test_should_find_correct_external_sensorname(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10405'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.3.0': 'SuperGoose II',
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
            '.1.3.6.1.4.1.17373.3.4.1.3.1': 'SuperDuperGoose II',
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        assert goose._get_sensorname() == 'SuperDuperGoose II'
        assert goose.goosename == 'SuperGoose II'


class TestGeistWeatherGoose(object):
    def test_should_handle_a_geist_weathergoose_trap(self):
        assert wg.GeistWeatherGoose.can_handle('.1.3.6.1.4.1.21239.2.32767.0.10205')

    def test_should_handle_a_geist_weathergoose_remote_trap(self):
        assert wg.GeistWeatherGoose.can_handle('.1.3.6.1.4.1.21239.2.32767.0.10405')
