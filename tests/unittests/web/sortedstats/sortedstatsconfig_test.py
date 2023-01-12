from mock import patch
import mock
from unittest import TestCase
from nav.web.sortedstats.config import SortedStatsConfig


class TestSortedStatsConfif(TestCase):
    def setUp(self):
        pass

    def test_correct_config_should_pass(self):
        config = u"""
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
