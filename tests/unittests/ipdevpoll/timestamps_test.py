"""Tests for ipdevpoll's TimestampChecker utility class"""

from mock import Mock, patch

import pytest
import pytest_twisted

from nav.ipdevpoll.timestamps import TimestampChecker


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_invalid_serialized_value_should_be_interpreted_as_change():
    ts = TimestampChecker(Mock(), Mock(), 'uptime')
    invalid_time_pickle = 'foobar'
    with patch(
        'nav.models.manage.NetboxInfo.objects.get', return_value=invalid_time_pickle
    ):
        yield ts.load()
        assert ts.is_changed()


@pytest.mark.twisted
@pytest_twisted.inlineCallbacks
def test_representation_inconsistencies_should_not_matter():
    """Tests that loaded and collected timestamps can be compared, even if the internal
    and the persisted representations may differ between being tuples and lists.

    The internal representation was always with tuples, but the new JSON-based db
    persistence converts this to lists, since tuples don't exist in JSON.
    """
    ts = TimestampChecker(Mock(), Mock(), 'sometime')
    json_data = "[[1559907627.0, 28245286]]"
    ts.collected_times = ((1559907627.0, 28245286),)
    mock_info = Mock(value=json_data)
    with patch('nav.models.manage.NetboxInfo.objects.get', return_value=mock_info):
        yield ts.load()
        assert not ts.is_changed(max_deviation=60)


@pytest.mark.parametrize(
    "loaded, collected, max_deviation, expected, description",
    [
        ((1559904661.0, 0), (1559904661.0, 0), 60, False, "identical timestamps"),
        ((1559904661.0, 0), (1559904671.0, 1000), 60, False, "10 seconds have passed"),
        (
            (1559904661.0, 0),
            (1559904760.0, 0),
            100,
            False,
            "deviation less than 100 seconds is acceptable",
        ),
        (
            (1559904661.0, 0),
            (1559905661.0, 1000),
            60,
            True,
            "1000 seconds have passed, but only 10 on agent",
        ),
        (
            None,
            (1559904671.0, 424242),
            60,
            True,
            "no previously saved timestamps were available",
        ),
    ],
)
def test_is_changed(loaded, collected, max_deviation, expected, description):
    ts = TimestampChecker(Mock(), Mock(), 'sometime')
    ts.loaded_times = [loaded] if loaded else None
    ts.collected_times = [collected]
    assert ts.is_changed(max_deviation=max_deviation) == expected, description
