from nav.event import Event
from nav.models.event import EventQueue


class TestEvent:
    def test_should_post_simple_event_without_error(self, localhost_using_legacy_db):
        event = Event(
            source='ipdevpoll',
            target='eventEngine',
            netboxid=localhost_using_legacy_db,
            eventtypeid='snmpAgentState',
            state=EventQueue.STATE_START,
        )

        assert event.post()
