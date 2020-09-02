from datetime import time, datetime
from mock import Mock
from nav.alertengine.base import _calculate_timeperiod_start


def test_calculate_timeperiod_start_should_detect_period_starting_yesterday():
    mock_now = datetime(year=2020, month=8, day=1, hour=7, minute=50)
    timeperiod = Mock(start=time(hour=8, minute=0))
    result = _calculate_timeperiod_start(timeperiod, now=mock_now)
    assert result.date() < mock_now.date()


def test_calculate_timeperiod_start_should_detect_period_starting_today():
    mock_now = datetime(year=2020, month=8, day=1, hour=8, minute=50)
    timeperiod = Mock(start=time(hour=8, minute=0))
    result = _calculate_timeperiod_start(timeperiod, now=mock_now)
    assert result.date() == mock_now.date()
