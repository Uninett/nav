import pytest
from unittest import TestCase
from unittest.mock import patch
from nav.metrics.names import (
    join_series,
    escape_metric_name,
    get_expanded_nodes,
    safe_name,
)


class MetricNamingTests(TestCase):
    def test_join_series(self):
        series1 = 'nav.zaphod.banana'
        series2 = 'nav.arthur.banana'
        result = join_series([series1, series2])
        self.assertEqual(result, 'nav.{zaphod,arthur}.banana')

    def test_join_single_series_should_return_same(self):
        series = 'oh.freddled.gruntbuggly'
        self.assertEqual(join_series([series]), series)


class TestGetExpandedNodes:
    def test_when_valid_response_should_return_results(self):
        raw_response = {
            "results": [
                "nav.foo.1",
                "nav.foo.2",
                "nav.foo.3",
                "nav.bar.baz",
            ]
        }

        with patch("nav.metrics.names.raw_metric_query", return_value=raw_response):
            assert get_expanded_nodes("whatever.path") == raw_response["results"]

    @pytest.mark.parametrize("raw_response", [[], {}, "foo", "", {"results": "foo"}])
    def test_when_invalid_response_should_return_empty_list(self, raw_response):
        with patch("nav.metrics.names.raw_metric_query", return_value=raw_response):
            assert get_expanded_nodes("whatever.path") == []


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
    ],
)
class TestEscapeMetricName:
    def test_should_escape_by_default(self, test_input, expected):
        assert escape_metric_name(test_input) == expected

    def test_should_not_escape_safe_names(self, test_input, expected):
        assert escape_metric_name(safe_name(test_input)) == str(test_input)
        assert escape_metric_name(str(safe_name(test_input))) == str(test_input)
