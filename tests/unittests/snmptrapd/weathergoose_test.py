from unittest import TestCase
from mock import patch, Mock

from nav.snmptrapd.handlers import weathergoose as wg


class WeatherGoose1ClassTest(TestCase):
    def test_should_not_handle_a_weathergoose2_trap(self):
        self.assertFalse(
            wg.WeatherGoose1.can_handle('.1.3.6.1.4.1.17373.3.32767.0.10205'))

    def test_should_handle_a_weathergoose1_trap(self):
        self.assertTrue(
            wg.WeatherGoose1.can_handle('.1.3.6.1.4.1.17373.0.10205'))

    def test_should_map_oid_to_correct_trigger(self):
        self.assertEqual(
            wg.WeatherGoose1.map_oid_to_trigger('.1.3.6.1.4.1.17373.0.10205'),
            'cmClimateTempCTRAP')

    def test_init_should_raise_on_invalid_oid(self):
        trap = Mock(snmpTrapOID = '5')
        self.assertRaises(Exception, wg.WeatherGoose1, trap, None, None, None)


class WeatherGoose1TrapTest(TestCase):
    def setUp(self):
        super(WeatherGoose1TrapTest, self).setUp()
        trap = Mock(snmpTrapOID = '.1.3.6.1.4.1.17373.0.10205')
        TRIP_TYPE_HIGH = 2
        self.goosename = 'cleese'
        self.temperature = 32
        trap.varbinds = {'.1.3.6.1.4.1.17373.2.1.6': TRIP_TYPE_HIGH,
                         '.1.3.6.1.4.1.17373.2.2.1.3.1': self.goosename,
                         '.1.3.6.1.4.1.17373.2.2.1.5.1': self.temperature}
        self.trap = trap

        class Event(dict):
            def post(self):
                pass

        self.event = patch('nav.event.Event', side_effect=Event)
        self.event.start()

    def tearDown(self):
        super(WeatherGoose1TrapTest, self).tearDown()
        self.event.stop()

    def test_init_should_parse_trap_without_error(self):
        self.assertTrue(wg.WeatherGoose1(self.trap, None, None, None))

    def test_should_find_correct_alert_type(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose._get_alert_type(), 'cmClimateTempCTRAP')

    def test_should_find_correct_goosename(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose.goosename, self.goosename)

    def test_should_find_climate_values(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose.climatevalue, self.temperature)

    def test_should_find_triptype_high(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose.triptype, 'High')

    def test_event_event_post(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertTrue(goose.post_event())

    def test_should_find_correct_sensorname(self):
        goose = wg.WeatherGoose1(self.trap, None, None, None)
        self.assertEquals(goose._get_sensorname(), 'cleese')


class WeatherGoose2Test(TestCase):
    def test_should_not_handle_a_weathergoose1_trap(self):
        self.assertFalse(
            wg.WeatherGoose2.can_handle('.1.3.6.1.4.1.17373.0.10205'))

    def test_should_handle_a_weathergoose2_trap(self):
        self.assertTrue(
            wg.WeatherGoose2.can_handle('.1.3.6.1.4.1.17373.3.32767.0.10205'))

    def test_should_handle_a_weathergoose2_remote_trap(self):
        self.assertTrue(
            wg.WeatherGoose2.can_handle('.1.3.6.1.4.1.17373.3.32767.0.10405'))

    def test_should_map_oid_to_correct_trigger(self):
        self.assertEqual(
            wg.WeatherGoose2.map_oid_to_trigger(
                '.1.3.6.1.4.1.17373.3.32767.0.10205'),
            'cmClimateTempCNOTIFY')

    def test_should_map_oid_to_correct_trigger_for_remote(self):
        self.assertEqual(
            wg.WeatherGoose2.map_oid_to_trigger(
                '.1.3.6.1.4.1.17373.3.32767.0.10405'),
            'cmTempSensorTempCNOTIFY')

    def test_should_find_correct_alert_type(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {'.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH}
        goose = wg.WeatherGoose2(trap, None, None, None)
        self.assertEquals(goose._get_alert_type(), 'cmClimateTempCNOTIFY')

    def test_should_find_correct_alert_type_remote(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10405'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {'.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH}
        goose = wg.WeatherGoose2(trap, None, None, None)
        self.assertEquals(goose._get_alert_type(), 'cmTempSensorTempCNOTIFY')

    def test_should_add_subid_when_alarminstance_defined(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
            '.1.3.6.1.4.1.17373.3.1.12.0': 4
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        self.assertEquals(goose._get_subid(), 4)

    def test_should_not_add_subid_when_not_in_varbinds(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        self.assertEquals(goose._get_subid(), None)

    def test_should_find_correct_value_from_external_trap(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10405'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
            '.1.3.6.1.4.1.17373.3.4.1.5.1': 16,
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        self.assertEqual(goose._get_trigger_values()[0], 16)

    def test_should_find_correct_internal_sensorname(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10205'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.3.0': 'SuperGoose II',
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
            '.1.3.6.1.4.1.17373.3.2.1.3.1': 'SuperDuperGoose II'
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        self.assertEqual(goose._get_sensorname(), 'SuperDuperGoose II')
        self.assertEqual(goose.goosename, 'SuperGoose II')

    def test_should_find_correct_external_sensorname(self):
        trap = Mock('trap')
        trap.snmpTrapOID = '.1.3.6.1.4.1.17373.3.32767.0.10405'
        TRIP_TYPE_HIGH = 2
        trap.varbinds = {
            '.1.3.6.1.4.1.17373.3.1.3.0': 'SuperGoose II',
            '.1.3.6.1.4.1.17373.3.1.6.0': TRIP_TYPE_HIGH,
            '.1.3.6.1.4.1.17373.3.4.1.3.1': 'SuperDuperGoose II'
        }
        goose = wg.WeatherGoose2(trap, None, None, None)
        self.assertEqual(goose._get_sensorname(), 'SuperDuperGoose II')
        self.assertEqual(goose.goosename, 'SuperGoose II')


class GeistWeatherGooseTest(TestCase):
    def test_should_handle_a_geist_weathergoose_trap(self):
        self.assertTrue(wg.GeistWeatherGoose.can_handle(
            '.1.3.6.1.4.1.21239.2.32767.0.10205'))

    def test_should_handle_a_geist_weathergoose_remote_trap(self):
        self.assertTrue(wg.GeistWeatherGoose.can_handle(
            '.1.3.6.1.4.1.21239.2.32767.0.10405'))
