#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Metric threshold evaluation utilities.

Pseudo-rule example:

    dict(
        target='nav.devices.*.ports.if{In,Out}Octets',
        alert='>90%',
        clear='<80%',

        raw=False,
        period='-10min',
    )

Some ideas on how this should function:

Target is a seriesList expression. If raw=True, its raw value is used when
querying Graphite-web, otherwise it will be transformed according to NAV's
rules before querying (such as deriving traffic rates from counter values).
We query data from 'period' until now, and calculate the average value for that
period for each retrieved metric (possibly ignoring None values).

Each retrieved metric must then be mapped to a NAV object, if at all possible.
This is necessary for two purposes:

1. It may be necessary to calculate the threshold expression,
   e.g. when a relative threshold value is used (such as '>90%').
2. If a threshold alert needs to be generated, it must be associated with a
   NAV object to make it clear to the user what the subject of the alert is.

If there is an active threshold alert for an object, the clear expression
should be evaluated to see if the alert can be resolved. Otherwise,
the alert expression should be evaluated to see if a threshold alert must be
opened.

Other feedback received:

* It should be possible to evaluate thresholds by comparing against other
  metrics. E.g. if a maximum value of an object is logged somewhere,
  one should be able to compare the current value to this.
* The datapoint consolidation method should be customizable. Right now,
  average is used, but maximum/minimum may be interesting values as well.

This module should provide an API for evaluating threshold expressions.
Alerting is outside of the scope of this module.

"""

from datetime import timedelta
from functools import partial
import logging
import re

from nav.metrics.data import get_metric_average
from nav.metrics.graphs import get_metric_meta, extract_series_name


# Pattern to extract the ID of a metric from a series name returned in a
# Graphite render response.
from nav.metrics.lookup import lookup
from nav.models.manage import Interface


EXPRESSION_PATTERN = re.compile(
    r'^ \s* (?P<operator> [<>] ) \s* '
    r'(?P<value> ([+-])? [0-9]+(\.[0-9]+)? ) \s*'
    r'(?P<percent>%)? \s* $',
    re.VERBOSE,
)

DEFAULT_INTERVAL = timedelta(minutes=10)
MINUTE = timedelta(minutes=1).total_seconds()
DAY = timedelta(days=1).total_seconds()
YEAR = timedelta(days=365).total_seconds()

MEGA = 1e6

_logger = logging.getLogger(__name__)


class ThresholdEvaluator(object):
    """Threshold evaluator class.

    Usage example:

    >>> t = ThresholdEvaluator('nav.devices.*.ports.*.if{In,Out}Octets')
    >>> t.get_values()
    >>> t.evaluate('>50%')
    [('nav.devices.test-sw_example_org.ports.Gi1/1.ifOutOctets',
      989982359.3691884),
     ('nav.devices.test-sw_example_org.ports.Gi1/1.ifInOctets',
      824604510.7694222)]
    >>>

    """

    def __init__(self, target, period=DEFAULT_INTERVAL, raw=False):
        """
        :param target: A graphite target/seriesList to look at.
        :param period: How far back in historic data to look.
        :type period: datetime.timedelta
        :param raw: If True, the target is fed raw to Graphite, otherwise it is
                    evaluated and possibly transformed by NAV's rules first.
        """
        self.target = self.orig_target = target
        self.period = period
        self.raw = raw
        self.result = {}

        if not raw:
            meta = get_metric_meta(target)
            if meta:
                self.target = meta['target']

    def __repr__(self):
        return "{cls}({orig_target!r}, {period!r}, {raw!r})".format(
            cls=self.__class__.__name__, **vars(self)
        )

    def get_values(self):
        """
        Retrieves actual values from Graphite based on the evaluators target.
        """
        start = "-{0}".format(interval_to_graphite(self.period))
        averages = get_metric_average(
            self.target, start=start, end='now', ignore_unknown=True
        )
        _logger.debug(
            "retrieved %d values from graphite for %r, period %s: %r",
            len(averages),
            self.target,
            self.period,
            averages,
        )
        self.result = dict(
            (extract_series_name(key), dict(value=value))
            for key, value in averages.items()
        )
        return self.result

    def evaluate(self, expression, invert=False):
        """
        Evaluates expression for each of the retrieved values from the last
        call to get_values().

        :param expression: A comparison expression to evaluate against the
                           collected data. Example: '>20%'.
        :type expression: basestring
        :param invert: Invert the expression logic if True.

        :returns: A list of (metric, current_value) tuples for metrics whose
                  last retrieved current value matches the expression.
        """
        matcher = self._get_matcher(expression)
        result = [
            (metric, self.result[metric]['value'])
            for metric in self.result.keys()
            if bool(matcher(metric)) ^ bool(invert)
        ]
        return result

    def _get_matcher(self, expression):
        match = EXPRESSION_PATTERN.match(expression)
        if not match:
            raise InvalidExpressionError(expression)
        value = float(match.group('value'))
        percent = bool(match.group('percent'))
        oper = match.group('operator')
        if oper == '<':
            matcher = partial(self._lt, value, percent)
        else:
            matcher = partial(self._gt, value, percent)
        return matcher

    def _gt(self, value, percent, metric):
        current = self._calculate_current(percent, metric)
        if current is not None:
            return current > value

    def _lt(self, value, percent, metric):
        current = self._calculate_current(percent, metric)
        if current is not None:
            return current < value

    def _calculate_current(self, percent, metric):
        if metric in self.result:
            current = self.result[metric]['value']
            if percent:
                maximum = get_metric_maximum(metric)
                if not maximum:
                    return None  # cannot relatively match a maximum=0
                self.result[metric]['max'] = maximum
                current = (current / maximum) * 100.0
            return current


def get_metric_maximum(metric):
    """
    Returns the maximum value of a metric, if one can be determined.
    Otherwise returns None.
    """
    obj = lookup(metric)
    if isinstance(obj, Interface):
        counter = metric.split('.')[-1]
        if 'octets' in counter.lower():
            # Making an unsafe assumption that interface traffic
            # numbers are always retrieved in bits/s
            maximum = obj.speed * MEGA
            if maximum:
                return maximum


class InvalidExpressionError(Exception):
    """Invalid threshold match expression"""

    pass


def interval_to_graphite(delta):
    """Converts a timedelta to a usable Graphite time specification.

    :type delta: datetime.timedelta

    """
    secs = delta.total_seconds()
    if secs % YEAR == 0:
        return "{0}year".format(int(secs / YEAR))
    elif secs % DAY == 0:
        return "{0}day".format(int(secs / DAY))
    elif secs % MINUTE == 0:
        return "{0}min".format(int(secs / MINUTE))
    else:
        return "{0}s".format(int(secs))
