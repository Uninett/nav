from nav.models.event import (
    AlertHistory,
    EventMixIn,
    ThresholdEvent,
    EventQueue,
    UnknownEventSubject,
)
from nav.models.manage import Interface
from mock import Mock, patch
import pytest


class TestEventMixIn(object):
    def test_subidless_netbox_event_should_return_netbox_subject(self, event):
        event.event_type_id = 'boxState'

        assert event.get_subject() is event.netbox

    def test_linkstate_event_should_return_interface_subject(self, event):
        event.event_type_id = 'linkState'
        event.subid = '42'

        expected_interface = Mock()
        with patch(
            "nav.models.manage.Interface.objects.get",
            return_value=expected_interface,
        ):
            assert event.get_subject() is expected_interface

    def test_thresholdstate_event_should_return_thresholdevent_object(self, event):
        event.event_type_id = 'thresholdState'
        event.subid = '42:some.random.metric'

        class MockedThresholdEvent(object):
            def __init__(self, *args, **kwargs):
                pass

        with patch("nav.models.event.ThresholdEvent", MockedThresholdEvent):
            assert isinstance(event.get_subject(), MockedThresholdEvent)

    def test_service_maintenance_event_should_return_service(self, event):
        event.event_type_id = 'maintenanceState'
        event.varmap = {
            EventQueue.STATE_START: {
                'service': 'http',
            }
        }
        event.subid = '42'

        expected_service = Mock()
        with patch(
            "nav.models.service.Service.objects.get",
            return_value=expected_service,
        ):
            assert event.get_subject() is expected_service

    def test_non_existent_subid_reference_should_return_unknown_event_subject(
        self,
        event,
    ):
        event.event_type_id = 'linkState'
        event.subid = '42'

        with patch(
            "nav.models.manage.Interface.objects.get",
            side_effect=Interface.DoesNotExist(),
        ):
            assert isinstance(event.get_subject(), UnknownEventSubject)

    def test_netboxless_event_should_return_device_subject(
        self,
        event,
    ):
        event.event_type_id = 'boxState'
        event.netbox = None

        assert event.get_subject() is event.device

    def test_netbox_and_deviceless_event_should_return_unknown_event_subject(
        self,
        event,
    ):
        event.event_type_id = 'boxState'
        event.netbox = None
        event.device = None

        assert isinstance(event.get_subject(), UnknownEventSubject)


def test_thresholdevent_should_lookup_thresholdrule(event):
    event.event_type_id = 'thresholdState'
    expected_metric = 'a.random.metric'
    event.subid = '42:' + expected_metric

    expected_rule = Mock()
    with patch(
        "nav.models.thresholds.ThresholdRule.objects.get",
        return_value=expected_rule,
    ):
        threvent = ThresholdEvent(event)
        assert threvent.rule is expected_rule
        assert threvent.metric == expected_metric


class TestAlertHistoryGetShortDescription:
    def test_when_sms_exists_it_should_return_sms_text(self, alert):
        self._add_message(alert, type='sms', message='Switch down')

        assert alert.get_short_description() == 'Switch down'

    def test_when_stateless_alert_it_should_use_stateless_state(self, alert):
        alert.end_time = None
        self._add_message(alert, type='sms', state='x', message='Threshold exceeded')

        assert alert.get_short_description() == 'Threshold exceeded'

    def test_when_no_sms_but_email_with_subject_it_should_return_subject(self, alert):
        self._add_message(
            alert,
            type='email',
            message='Subject: Router gw1 is down\n\nDetails here...',
        )

        assert alert.get_short_description() == 'Router gw1 is down'

    def test_when_email_subject_has_extra_whitespace_it_should_strip_it(self, alert):  # noqa: E501
        self._add_message(
            alert,
            type='email',
            message='Subject:   Router gw1 is down  \n\nBody text',
        )

        assert alert.get_short_description() == 'Router gw1 is down'

    def test_when_email_has_no_subject_it_should_fall_through(self, alert):
        self._add_message(
            alert,
            type='email',
            message='Just a plain message body',
        )
        alert.alert_type = Mock(description='boxDown')

        assert alert.get_short_description() == 'boxDown'

    def test_when_no_messages_it_should_return_alert_type_description(self, alert):
        alert.alert_type = Mock(description='boxDown')

        assert alert.get_short_description() == 'boxDown'

    def test_when_no_messages_and_no_alert_type_it_should_return_empty_string(
        self, alert
    ):  # noqa: E501
        alert.alert_type = None

        assert alert.get_short_description() == ""

    def test_when_sms_exists_it_should_be_preferred_over_email(self, alert):
        self._add_message(alert, type='sms', message='Switch down')
        self._add_message(
            alert,
            type='email',
            message='Subject: Switch gw1 is down\n\nLong body...',
        )

        assert alert.get_short_description() == 'Switch down'

    def test_when_language_specified_it_should_filter_by_language(self, alert):
        self._add_message(alert, type='sms', language='nb', message='Svitsj nede')

        assert alert.get_short_description(language='nb') == 'Svitsj nede'

    @staticmethod
    def _add_message(alert, type='sms', language='en', state='s', message='test'):
        """Adds a mock message to the alert's message filter chain."""
        msg = Mock()
        msg.type = type
        msg.language = language
        msg.state = state
        msg.message = message
        alert._messages.append(msg)

    @pytest.fixture
    def alert(self):
        alert = Mock(spec=AlertHistory)
        alert.end_time = 'infinity'
        alert.alert_type = None
        alert._messages = []

        def filter_side_effect(**kwargs):
            result = Mock()
            for msg in alert._messages:
                if all(getattr(msg, k) == v for k, v in kwargs.items()):
                    result.first.return_value = msg
                    return result
            result.first.return_value = None
            return result

        alert.messages = Mock()
        alert.messages.filter.side_effect = filter_side_effect
        alert.get_short_description = AlertHistory.get_short_description.__get__(alert)
        return alert


#
# Fixtures
#


@pytest.fixture
def event():
    e = EventMixIn()
    e.event_type_id = None
    e.netbox = object()
    e.device = object()
    e.subid = None
    return e
