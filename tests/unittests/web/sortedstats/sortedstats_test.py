import datetime
from mock import patch
import mock
from unittest import TestCase

import nav.web.sortedstats.views as views


class TestSortedStats(TestCase):
    def setUp(self):
        pass

    def timestamp_to_datetime(self, timestamp):
        return datetime.datetime.strptime(timestamp, views.GRAPHITE_TIME_FORMAT)

    def test_get_timestamps_has_correct_delta(self):
        start_ts, end_ts = views.get_timestamps('hour')
        start_dt = self.timestamp_to_datetime(start_ts)
        end_dt = self.timestamp_to_datetime(end_ts)
        self.assertEqual(end_dt - start_dt, datetime.timedelta(hours=1))

    def test_cache_key_is_correct(self):
        view = "view1"
        timeframe = "hour"
        rows = 5
        expected_cache_key = "view1_hour_5"
        cache_key = views.get_cache_key(view, timeframe, rows)
        self.assertEqual(cache_key, expected_cache_key)
