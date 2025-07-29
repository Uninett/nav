#
# Copyright (C) 2021 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Contains functionality for eventengine to parse user-configured alert severity
modification rules and apply them to generated alerts.

To load a set of rules from a YAML config file, you can do:

    rules = SeverityRules.load_from_file("my_config_file.yml")

Then, given an alert object you wish to assign a new severity value to:

    new_severity = rules.evaluate(alert)
    alert.severity = new_severity
    alert.save()

"""

from operator import attrgetter
import logging
import typing
import yaml

from nav import config
from nav.models import event

__all__ = ["Severity", "SeverityRules"]
#
# Module constants
#


DEFAULT_SEVERITY = 3  # middle of the road
CONFIG_FILE = "severity.yml"
_logger = logging.getLogger(__name__)

#
# Type definitions used in this module
#


class Expression(typing.NamedTuple):
    """An alert attribute matching expression"""

    attr: typing.Union[str, callable]
    value: typing.Any


SeverityModifier = typing.Callable[[int], int]
Expressions = typing.Union[tuple[Expression], tuple]
Rule = tuple[Expressions, SeverityModifier]
AlertObject = typing.Union[event.EventQueue, event.AlertQueue, event.AlertHistory]

#
# Class definitions
#


class Severity(int):
    """Integer subclass that will not allow values outside the interval [1,5]"""

    def __new__(cls, *args, **kwargs):
        value = max(min(int(args[0]), 5), 1)
        return super(Severity, cls).__new__(cls, value)

    def __add__(self, value: int):
        return self.__class__(int(self) + value)

    def __sub__(self, value: int):
        return self.__class__(int(self) - value)


class SeverityRules(tuple):
    """An ordered sequence of evaluateable severity modification rules.

    An instance of this class represents an immutable, ordered sequence of rules to
    match alert objects and assign new severity value to them. It provides the
    evaluate() method to evaluate the sequence of rules in the context of any given
    alert object.
    """

    def __new__(cls, rules: typing.Sequence[Rule]):
        translated_rules = (cls._translate_rule(r) for r in rules)
        return super().__new__(cls, translated_rules)

    @classmethod
    def load_from_file(cls, filename: str = CONFIG_FILE) -> 'SeverityRules':
        """Instantiates a SeverityRules object from rule definitions in a YAML file"""
        full_path = config.find_config_file(filename)
        if not full_path:
            _logger.debug("could not find severity config file %s", filename)
            return None
        else:
            _logger.debug("loading severity rules from %s", full_path)

        with open(full_path) as conf:
            return cls.load(conf)

    @classmethod
    def load(cls, string_or_stream: typing.Union[str, typing.IO]) -> 'SeverityRules':
        """Instantiates a new SeverityRules object from YAML rule definitions"""
        raw_data = yaml.safe_load(string_or_stream) or {}
        rules = cls._parse_raw_severity_rules(raw_data)
        return cls(rules)

    def evaluate(self, alert: AlertObject) -> Severity:
        """Evaluates this set of rules using the supplied alert object as context,
        returning the resulting severity value.
        """
        _logger.debug("evaluating rules against %r", alert)
        severity = getattr(alert, "severity", DEFAULT_SEVERITY)
        for expressions, modifier in self:
            checks = (expr.attr(alert) == expr.value for expr in expressions)
            try:
                if all(checks):
                    _logger.debug("Matched %r", expressions)
                    severity = modifier(severity)
                else:
                    _logger.debug("%r did NOT match", expressions)
            except AttributeError as error:
                _logger.error(
                    "severity rule tried to access invalid attribute: %s", error
                )
        return severity

    @classmethod
    def _parse_raw_severity_rules(
        cls, definitions: dict
    ) -> typing.Generator[Rule, None, None]:
        """Generator that parses a dictionary of severity rules as loaded from a YAML
        config file, and yields a chain of rules with matching expressions and
        corresponding severity modifiers.

        """
        default = definitions.get("default-severity")
        if default is None:
            # Use the alert's original severity value
            yield (), lambda x: Severity(x)
        else:
            default = Severity(default)
            yield (), lambda x: default

        yield from cls._parse_rule_sublist((), definitions.get("rules", []))

    @classmethod
    def _parse_rule_sublist(
        cls, current: Expressions, definitions: list[dict]
    ) -> typing.Generator[Rule, None, None]:
        """Generator that parses a nested list of severity rule definitions and their
        corresponding severity modifiers, yielding a list of tuples describing the
        rules to be applied.

        :param current: The current set of expressions that new expressions will begin
        with.
        :param definitions: The list of YAML-deserialized rule definitions to parse.
        """
        for ruledef in definitions:
            expr = current
            modifier = None
            for attr, value in ruledef.items():
                if attr == "severity":
                    try:
                        modifier = cls._parse_modifier(value)
                    except ValueError:
                        raise ValueError(
                            f"{value!r} is an invalid severity modifier expression"
                        ) from None
                elif attr == "rules":
                    continue
                else:
                    expr += (Expression(attr, value),)

            if modifier:
                yield expr, modifier
            if "rules" in ruledef:
                yield from cls._parse_rule_sublist(expr, ruledef.get("rules", []))

    @staticmethod
    def _parse_modifier(value: typing.Union[str, int]) -> SeverityModifier:
        """Parses a severity modifier expression and returns a modifier callable. The
        callable will take a severity value as an argument, and returns a modified
        severity value.
        """
        oper = None
        if isinstance(value, str):
            if value[0] in ("+", "-"):
                oper = value[0]
                value = int(value[1:])

        value = int(value)
        if oper == "+":
            return lambda x: x + value
        elif oper == "-":
            return lambda x: x - value
        else:
            return lambda x: Severity(value)

    @classmethod
    def _translate_rule(cls, rule: Rule):
        """Translates the attribute sequence of a Rule to attrgetter callables that
        will fetch those attributes from any object supplied as its argument.
        """
        expressions, modifier = rule
        if expressions == ():
            # empty expression list means: Alway apply / Always True
            new_expressions = (Expression(lambda x: True, True),)
        else:
            new_expressions = (
                Expression(attrgetter(e.attr), e.value) for e in expressions
            )
        return tuple(new_expressions), modifier
