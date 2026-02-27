"""Unit tests for EventEngine scheduler yield behavior"""

import time
from unittest.mock import Mock, patch

import pytest

from nav.eventengine.config import EventEngineConfig
from nav.eventengine.engine import EventEngine


class TestHasOverdueCallbacks:
    def test_when_queue_is_empty_it_should_return_false(self, engine):
        assert engine._has_overdue_callbacks() is False

    def test_when_entry_is_in_future_it_should_return_false(self, engine):
        engine._scheduler.enter(1000, 0, lambda: None, ())
        assert engine._has_overdue_callbacks() is False

    def test_when_entry_is_past_due_it_should_return_true(self, engine):
        engine._scheduler.enter(0, 0, lambda: None, ())
        future = time.time() + 10
        with patch("time.time", return_value=future):
            assert engine._has_overdue_callbacks() is True


class TestLoadNewEventsYieldBehavior:
    """Tests for the yield-to-scheduler logic inside load_new_events()"""

    @patch("nav.eventengine.engine.unresolved")
    def test_when_nothing_is_overdue_then_load_new_events_should_process_all_events(
        self, mock_unresolved, engine
    ):
        events = [_make_fake_event(i) for i in range(1, 4)]

        with (
            patch("nav.eventengine.engine.Event.objects") as mock_objects,
            patch.object(engine, "handle_event") as mock_handle,
            patch.object(engine, "_has_overdue_callbacks", return_value=False),
            patch.object(engine, "_schedule_next_queuecheck") as mock_reschedule,
        ):
            mock_objects.filter.return_value.order_by.return_value = events
            engine.load_new_events.__wrapped__.__wrapped__(engine)

            assert mock_handle.call_count == 3
            mock_reschedule.assert_not_called()

    @patch("nav.eventengine.engine.unresolved")
    def test_when_callbacks_are_overdue_then_load_new_events_should_break_early(
        self, mock_unresolved, engine
    ):
        events = [_make_fake_event(i) for i in range(1, 4)]

        with (
            patch("nav.eventengine.engine.Event.objects") as mock_objects,
            patch.object(engine, "handle_event") as mock_handle,
            patch.object(
                engine,
                "_has_overdue_callbacks",
                side_effect=[False, True],
            ),
            patch.object(engine, "_schedule_next_queuecheck") as mock_reschedule,
        ):
            mock_objects.filter.return_value.order_by.return_value = events
            engine.load_new_events.__wrapped__.__wrapped__(engine)

            assert mock_handle.call_count == 2
            mock_reschedule.assert_called_once()

    @patch("nav.eventengine.engine.unresolved")
    def test_when_resumed_after_yield_then_load_new_events_should_process_remaining(
        self, mock_unresolved, engine
    ):
        events = [_make_fake_event(i) for i in range(1, 4)]

        def track_as_unfinished(event):
            engine._unfinished.add(event.id)

        with (
            patch("nav.eventengine.engine.Event.objects") as mock_objects,
            patch.object(
                engine, "handle_event", side_effect=track_as_unfinished
            ) as mock_handle,
            patch.object(
                engine,
                "_has_overdue_callbacks",
                side_effect=[False, True],
            ),
            patch.object(engine, "_schedule_next_queuecheck"),
        ):
            mock_objects.filter.return_value.order_by.return_value = events
            engine.load_new_events.__wrapped__.__wrapped__(engine)
            assert mock_handle.call_count == 2

        # Second run: all 3 events still in queue, but the 2 already handled
        # are in _unfinished, so only event 3 is new
        with (
            patch("nav.eventengine.engine.Event.objects") as mock_objects,
            patch.object(engine, "handle_event") as mock_handle,
            patch.object(engine, "_has_overdue_callbacks", return_value=False),
            patch.object(engine, "_schedule_next_queuecheck"),
        ):
            mock_objects.filter.return_value.order_by.return_value = events
            engine.load_new_events.__wrapped__.__wrapped__(engine)
            assert mock_handle.call_count == 1
            mock_handle.assert_called_once_with(events[2])


@pytest.fixture
def engine():
    config = EventEngineConfig()
    config.DEFAULT_CONFIG_FILES = ()
    return EventEngine(config=config)


def _make_fake_event(event_id, event_type_id="boxState"):
    event = Mock()
    event.id = event_id
    event.event_type_id = event_type_id
    event.netbox = Mock()
    return event
