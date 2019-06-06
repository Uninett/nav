import pytest
from unittest import TestCase
from nav.metrics.names import join_series, escape_metric_name


class MetricNamingTests(TestCase):
    def test_join_series(self):
        series1 = 'nav.zaphod.banana'
        series2 = 'nav.arthur.banana'
        result = join_series([series1, series2])
        self.assertEqual(result, 'nav.{zaphod,arthur}.banana')

    def test_join_single_series_should_return_same(self):
        series = 'oh.freddled.gruntbuggly'
        self.assertEqual(join_series([series]), series)


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (None, None),
        ('', ''),
        ('foobar', 'foobar'),
        ('strangeness\x00', 'strangeness'),
        ('dot.warner', 'dot_warner'),
        ('ge-1/0/0.1', 'ge-1_0_0_1'),
        ('temperature [chassis 1]', 'temperature__chassis_1_'),
        ('something in (parens)', 'something_in__parens_'),
        ('temperature, top', 'temperature__top'),
    ]
)
def test_escape_metric_name(test_input, expected):
    assert escape_metric_name(test_input) == expected
