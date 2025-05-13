from mock import patch
from unittest import TestCase
from nav.web.sortedstats.config import SortedStatsConfig


class TestSortedStatsConfif(TestCase):
    def setUp(self):
        pass

    def test_correct_config_should_pass(self):
        config = """
            [myreport]
            view=cpu_routers_highestmax
            timeframe=hour
            rows=5
            """
        expected_reports = {
            'myreport': {
                'timeframe': 'hour',
                'view': 'cpu_routers_highestmax',
                'rows': 5,
            }
        }
        with patch.object(SortedStatsConfig, 'DEFAULT_CONFIG', config):
            conf = SortedStatsConfig()
            reports = conf.get_reports('hour')
        self.assertEqual(reports, expected_reports)

    def test_config_ignores_other_timestamps(self):
        config = """
            [myreport]
            view=cpu_routers_highestmax
            timeframe=day
            rows=5
            """
        with patch.object(SortedStatsConfig, 'DEFAULT_CONFIG', config):
            conf = SortedStatsConfig()
            reports = conf.get_reports('hour')
        self.assertEqual(reports, dict())

    def test_invalid_config_returns_no_report(self):
        config = """
            [myreport]
            view=cpu_routers_highestmax
            timeframe=invalid
            rows=5
            """
        with patch.object(SortedStatsConfig, 'DEFAULT_CONFIG', config):
            conf = SortedStatsConfig()
            reports = conf.get_reports('hour')
        self.assertEqual(reports, dict())

    def test_invalid_timeframe_should_raise_exception(self):
        conf = SortedStatsConfig()
        with self.assertRaises(ValueError):
            conf.validate_timeframe('invalid_timeframe')

    def test_invalid_view_should_raise_exception(self):
        conf = SortedStatsConfig()
        with self.assertRaises(ValueError):
            conf.validate_timeframe('invalid_view')

    def test_invalid_rows_should_raise_exception(self):
        conf = SortedStatsConfig()
        with self.assertRaises(ValueError):
            conf.validate_timeframe(0)
