import pytest
from nav.eventengine.severity import Severity


class TestThatSeverity:
    def test_should_never_instantiate_to_higher_than_5(self):
        assert Severity(32) == 5

    def test_should_never_instantiate_to_lower_than_1(self):
        assert Severity(0) == 1
        assert Severity(-13) == 1

    @pytest.mark.parametrize("value", range(1, 6))
    def test_should_retain_all_values_from_1_to_5(self, value):
        assert Severity(value) == value

    def test_should_not_add_to_values_above_5(self):
        assert (Severity(3) + 42) == 5

    def test_should_not_subtract_to_values_below_1(self):
        assert (Severity(3) - 42) == 1
