from nav.models.event import (
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
