from contextlib import nullcontext
from unittest.mock import Mock

import pytest

from nav.ipdevpoll.plugins import psuwatch
from nav.ipdevpoll.plugins.psuwatch import (
    PowerSupplyOrFanStateWatcher,
    STATE_DOWN,
    STATE_UNKNOWN,
    STATE_UP,
    STATE_WARNING,
)


@pytest.fixture
def factory():
    """A stand-in event factory whose start/end produce mock events."""
    fake = Mock()
    fake.start.return_value = Mock(name="start_event")
    fake.end.return_value = Mock(name="end_event")
    return fake


@pytest.fixture
def watcher(monkeypatch, factory):
    """A watcher wired up to post events through the fake factory only."""
    monkeypatch.setattr(psuwatch, "EVENT_MAP", {"powerSupply": factory})
    monkeypatch.setattr(psuwatch.transaction, "atomic", lambda: nullcontext())

    return object.__new__(PowerSupplyOrFanStateWatcher)


def _unit():
    return Mock(
        physical_class="powerSupply",
        name="Power Supply B",
        id=1,
        device_id=None,
        netbox=Mock(sysname="switch.example.org"),
    )


class TestPostEvent:
    def test_should_not_alert_when_never_observed_working(self, watcher, factory):
        """An empty bay goes straight from UNKNOWN to DOWN and must not alert."""
        watcher._post_event(_unit(), STATE_UNKNOWN, STATE_DOWN)
        factory.start.assert_not_called()
        factory.end.assert_not_called()

    def test_should_alert_when_working_unit_goes_down(self, watcher, factory):
        """A real PSU that was UP and fails must raise a start (psuNotOK) event."""
        watcher._post_event(_unit(), STATE_UP, STATE_DOWN)
        factory.start.assert_called_once()
        factory.start.return_value.save.assert_called_once()

    def test_should_alert_when_working_unit_warns(self, watcher, factory):
        watcher._post_event(_unit(), STATE_UP, STATE_WARNING)
        factory.start.assert_called_once()

    def test_should_resolve_when_unit_comes_back_up(self, watcher, factory):
        """A recovery must raise an end (psuOK) event regardless of prior state."""
        watcher._post_event(_unit(), STATE_DOWN, STATE_UP)
        factory.end.assert_called_once()
        factory.end.return_value.save.assert_called_once()
