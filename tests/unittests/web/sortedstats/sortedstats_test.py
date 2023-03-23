import datetime
from mock import patch, MagicMock
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
        view = "uptime"
        timeframe = "hour"
        rows = 5
        expected_cache_key = "uptime_hour_5"
        cache_key = views.get_cache_key(view, timeframe, rows)
        self.assertEqual(cache_key, expected_cache_key)

    @patch('nav.web.sortedstats.views.get_cache')
    def test_process_form_returns_cache_value_if_cache_exists(self, cache_mock):
        data = "cached"
        cache_mock.return_value.get.return_value.data = data
        fake_form = MagicMock()
        fake_form.cleaned_data = {
            'view': 'uptime',
            'timeframe': 'hour',
            'rows': 5,
            'use_cache': True,
        }
        result, from_cache = views.process_form(fake_form)
        self.assertTrue(from_cache)
        self.assertEqual(result.data, data)

    @patch('nav.web.sortedstats.views.collect_result')
    @patch('nav.web.sortedstats.views.get_cache')
    def test_cache_not_used_if_empty_and_use_cache_is_on(
        self, cache_mock, collect_mock
    ):
        data = "new"
        cache_mock.return_value.get.return_value.data = ""
        collect_mock.return_value.data = data
        fake_form = MagicMock()
        fake_form.cleaned_data = {
            'view': 'uptime',
            'timeframe': 'hour',
            'rows': 5,
            'use_cache': True,
        }
        result, from_cache = views.process_form(fake_form)
        self.assertFalse(from_cache)
        self.assertEqual(result.data, data)

    @patch('nav.web.sortedstats.views.collect_result')
    @patch('nav.web.sortedstats.views.get_cache')
    def test_cache_not_used_if_empty_and_use_cache_is_off(
        self, cache_mock, collect_mock
    ):
        data = "new"
        cache_mock.return_value.get.return_value.data = ""
        collect_mock.return_value.data = data
        fake_form = MagicMock()
        fake_form.cleaned_data = {
            'view': 'uptime',
            'timeframe': 'hour',
            'rows': 5,
            'use_cache': False,
        }
        result, from_cache = views.process_form(fake_form)
        self.assertFalse(from_cache)
        self.assertEqual(result.data, data)
