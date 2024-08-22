"""Unit tests for nav.metrics.thresholds"""

from nav.metrics.thresholds import ThresholdEvaluator


class TestThatThresholdEvaluator:
    def test_evaluates_zero_as_less_than_positive_number(self):
        """A regression test for #2447"""
        t = ThresholdEvaluator('data.*')
        t.result = {
            'data.good': {'value': 200.0},
            'data.zero': {'value': 0.0},
        }

        assert ('data.zero', 0.0) in t.evaluate('<120')

    def test_evaluates_zero_as_greater_than_negative_number(self):
        """A regression test for #2447"""
        t = ThresholdEvaluator('data.*')
        t.result = {
            'data.good': {'value': -50.0},
            'data.zero': {'value': 0.0},
        }

        assert ('data.zero', 0.0) in t.evaluate('>-120')
