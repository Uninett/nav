import pytest
from mock import Mock
import yaml

from nav.eventengine.severity import (
    Severity,
    Expression,
    SeverityRules,
)


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


class TestThatSeverityParser:
    """Tests for the internal parsing methods of the SeverityRules class"""

    def test_should_return_original_severity_on_empty_ruleset(self):
        rules = SeverityRules._parse_raw_severity_rules({})
        expressions, modifier = next(rules)
        assert expressions == ()
        assert modifier(5) == 5

    def test_should_load_simple_ruleset_without_error(self, simple_severity_ruleset):
        assert list(SeverityRules._parse_raw_severity_rules(simple_severity_ruleset))

    def test_should_parse_default_severity_correctly(self, simple_severity_ruleset):
        rules = SeverityRules._parse_raw_severity_rules(simple_severity_ruleset)
        expressions, modifier = next(rules)
        assert expressions == ()
        assert modifier(None) == 2, "first rule isn't the default severity level"

    def test_should_find_perfectly_cromulent_rule(self, simple_severity_ruleset):
        rules = SeverityRules._parse_raw_severity_rules(simple_severity_ruleset)
        _ = next(rules)  # toss default severity level rule
        expressions, modifier = next(rules)
        assert expressions == (Expression("foo", "perfectly-cromulent"),), (
            "the second rule in the ruleset was not parsed correctly"
        )
        assert callable(modifier)

    def test_should_parse_nested_rule_correctly(self, nested_severity_ruleset):
        rules = SeverityRules._parse_raw_severity_rules(nested_severity_ruleset)
        _ = next(rules), next(rules)  # skip two first rules
        expressions, modifier = next(rules)
        assert expressions == (
            Expression("first", "level-one"),
            Expression("second", "level-two"),
        ), "could not find a properly parsed nested rule"
        assert callable(modifier)

    def test_should_parse_compound_rule_correctly(self, nested_severity_ruleset):
        rules = SeverityRules._parse_raw_severity_rules(nested_severity_ruleset)
        _ = next(rules), next(rules), next(rules)  # skip first three
        expressions, modifier = next(rules)
        assert expressions == (
            Expression("foo", "0xc0ffee"),
            Expression("bar", "0xbadc0de"),
        ), "could not find a properly parsed compound rule"
        assert callable(modifier)

    def test_should_return_modifiers_that_take_int_and_return_int(
        self, nested_severity_ruleset
    ):
        for expressions, modifier in SeverityRules._parse_raw_severity_rules(
            nested_severity_ruleset
        ):
            assert callable(modifier), (
                f"modifier isn't callable for rule {expressions!r}"
            )
            assert isinstance(modifier(Severity(3)), int), (
                f"modifier does not follow protocol for rule {expressions!r}"
            )


class TestThatModifierParser:
    """Testing for the SeverityRules class internal parser of modifier strings"""

    def test_should_parse_int_correctly(self):
        modifier = SeverityRules._parse_modifier(3)
        assert modifier(None) == 3

    def test_should_parse_subtraction_correctly(self):
        modifier = SeverityRules._parse_modifier("-2")
        assert modifier(5) == 5 - 2

    def test_should_parse_addition_correctly(self):
        modifier = SeverityRules._parse_modifier("+2")
        assert modifier(1) == 1 + 2

    def should_raise_value_error_on_invalid_value(self):
        with pytest.raises(ValueError):
            SeverityRules._parse_modifier("foo")


class TestThatSeverityRules:
    """Tests for the external interface of the SeverityRules class"""

    def test_should_translate_ruleset_without_errors(
        self, simple_severity_ruleset_source
    ):
        assert SeverityRules.load(simple_severity_ruleset_source)

    def test_should_set_default_severity(self, simple_severity_ruleset_source):
        rules = SeverityRules.load(simple_severity_ruleset_source)
        alert = Mock()
        assert rules.evaluate(alert) == 2

    def test_should_add_to_severity_for_simple_rule(
        self, simple_severity_ruleset_source
    ):
        rules = SeverityRules.load(simple_severity_ruleset_source)
        alert = Mock()
        alert.foo = "perfectly-cromulent"
        assert rules.evaluate(alert) == 3

    def test_should_add_to_severity_for_nested_rule(
        self, nested_severity_ruleset_source
    ):
        rules = SeverityRules.load(nested_severity_ruleset_source)
        alert = Mock()
        alert.first = "level-one"
        alert.second = "level-two"
        assert rules.evaluate(alert) == 5

    def test_should_properly_set_severity_based_on_nested_attributes(
        self, nested_severity_ruleset_source
    ):
        rules = SeverityRules.load(nested_severity_ruleset_source)
        alert = Mock()
        alert.netbox.room.id = "Milliways"
        alert.netbox.room.location.id = "The end of the Universe"
        alert.netbox.category = "SW"
        assert rules.evaluate(alert) == 1

    def test_should_reset_severity_according_to_rule(
        self, nested_severity_ruleset_source
    ):
        rules = SeverityRules.load(nested_severity_ruleset_source)
        alert = Mock()
        alert.foo = "0xc0ffee"
        alert.bar = "0xbadc0de"
        assert rules.evaluate(alert) == 5

    def test_should_evaluate_to_single_rule_on_empty_rulesets(
        self, empty_ruleset_source
    ):
        """Tests that an empty ruleset is parsed into a single default-value rule"""
        rules = SeverityRules.load(empty_ruleset_source)
        assert len(rules) == 1

    def test_should_return_original_severity_when_no_default_is_set(
        self, empty_ruleset_source
    ):
        rules = SeverityRules.load(empty_ruleset_source)
        alert = Mock()
        alert.severity = 1
        assert rules.evaluate(alert) == 1

    def test_should_ignore_broken_rules(self, broken_ruleset_source):
        rules = SeverityRules.load(broken_ruleset_source)

        class MockAlert:
            """Simple Alert mock that does NOT ignore illegal attribute accesses"""

            severity = 5

        assert rules.evaluate(MockAlert()) == 5


#
# Fixtures
#
@pytest.fixture(scope="session")
def simple_severity_ruleset(simple_severity_ruleset_source):
    return yaml.safe_load(simple_severity_ruleset_source)


@pytest.fixture(scope="session")
def simple_severity_ruleset_source():
    return """
---
default-severity: 2
rules:
  - foo: perfectly-cromulent
    severity: '+1'
"""


@pytest.fixture(scope="session")
def nested_severity_ruleset(nested_severity_ruleset_source):
    return yaml.safe_load(nested_severity_ruleset_source)


@pytest.fixture(scope="session")
def nested_severity_ruleset_source():
    return """
---
default-severity: 2
rules:
  - first: level-one
    severity: '+1'
    rules:
    - second: level-two
      severity: '+2'
  - foo: '0xc0ffee'
    bar: '0xbadc0de'
    severity: 5
  - netbox.category: SW
    netbox.room.id: Milliways
    severity: '-1'
"""


@pytest.fixture(scope="session")
def empty_ruleset_source():
    return """
---
"""


@pytest.fixture(scope="session")
def broken_ruleset_source():
    return """
---
rules:
  - invalid-attribute: foo
    severity: 1
"""
