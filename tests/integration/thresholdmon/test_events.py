import pytest

from nav.models.thresholds import ThresholdRule
from nav import thresholdmon


def test_events(rule):
    assert thresholdmon.get_unresolved_threshold_alerts() == {}

    event = thresholdmon.start_event(rule, 'foo.bar', 2)
    assert event.state == event.STATE_START
    assert event.source_id == 'thresholdMon'
    assert event.target_id == 'eventEngine'
    assert event.event_type_id == 'thresholdState'

    event = thresholdmon.end_event(rule, 'foo.bar', 0)
    assert event.state == event.STATE_END
    assert event.source_id == 'thresholdMon'
    assert event.target_id == 'eventEngine'
    assert event.event_type_id == 'thresholdState'

    assert thresholdmon.get_unresolved_threshold_alerts() == {}


@pytest.fixture
def rule():
    rule = ThresholdRule(target='foo.bar>1', alert='high foobar')
    rule.save()
    yield rule
    rule.delete()
