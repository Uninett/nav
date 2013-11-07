from unittest import TestCase
from nav.metrics.names import join_series


class MetricNamingTests(TestCase):
    def test_join_series(self):
        series1 = 'nav.zaphod.banana'
        series2 = 'nav.arthur.banana'
        result = join_series([series1, series2])
        self.assertEqual(result, 'nav.{zaphod,arthur}.banana')

    def test_join_single_series_should_return_same(self):
        series = 'oh.freddled.gruntbuggly'
        self.assertEqual(join_series([series]), series)
