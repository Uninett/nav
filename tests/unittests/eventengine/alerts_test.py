from unittest import TestCase
import datetime
from nav.models.event import EventQueue as Event, Subsystem, EventType
from nav.models.manage import Netbox, Device
from nav.eventengine.alerts import AlertGenerator


class MockedAlertGenerator(AlertGenerator):
    def get_alert_type(self):
        return None

    def _find_existing_alert_history(self):
        return None


class AlertFromEventBase(TestCase):
    def setUp(self):
        self.event = Event(
            source=Subsystem('someone'),
            netbox=Netbox(),
            device=Device(),
            subid="thing",
            event_type=EventType('boxState'),
            state=Event.STATE_START,
            time=datetime.datetime.now(),
            value=50,
            severity=2,
        )


class AlertFromEventTests(AlertFromEventBase):
    def test_alert_from_event_copies_attributes(self):
        alert = MockedAlertGenerator(self.event).make_alert()

        self.assertEqual(alert.source, self.event.source)
        self.assertEqual(alert.netbox, self.event.netbox)
        self.assertEqual(alert.device, self.event.device)
        self.assertEqual(alert.subid, self.event.subid)
        self.assertEqual(alert.state, self.event.state)
        self.assertEqual(alert.time, self.event.time)
        self.assertEqual(alert.value, self.event.value)
        self.assertEqual(alert.severity, self.event.severity)

    def test_alert_from_event_copies_variables(self):
        self.event.varmap = dict(foo='bar', parrot='dead')
        alert = MockedAlertGenerator(self.event).make_alert()

        self.assertEqual(alert.varmap, self.event.varmap)


class AlertHistoryFromEventTests(AlertFromEventBase):
    def test_alerthist_from_event_copies_attributes(self):
        history = MockedAlertGenerator(self.event).make_alert_history()

        self.assertEqual(history.source, self.event.source)
        self.assertEqual(history.netbox, self.event.netbox)
        self.assertEqual(history.device, self.event.device)
        self.assertEqual(history.subid, self.event.subid)
        self.assertEqual(history.start_time, self.event.time)
        self.assertEqual(history.value, self.event.value)
        self.assertEqual(history.severity, self.event.severity)
        self.assertEqual(history.end_time, datetime.datetime.max)

    def test_should_not_create_alerthist_from_end_event(self):
        self.event.state = self.event.STATE_END
        alert = MockedAlertGenerator(self.event)
        self.assertTrue(alert.make_alert_history() is None)
