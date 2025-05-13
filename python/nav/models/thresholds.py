#
# Copyright (C) 2013 Uninett AS
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
"""Metric threshold related models"""

from datetime import timedelta
from django.db import models
from nav.metrics.graphs import extract_series_name, translate_serieslist_to_regex
from nav.models.profiles import Account
from nav.models.fields import VarcharField
from nav.metrics.thresholds import ThresholdEvaluator, DEFAULT_INTERVAL


class ThresholdRule(models.Model):
    """A threshold rule"""

    alert_help_text = """
    Examples: >20, <10. Percent (>20%) can only be used on interface octet
    counters.
    """

    id = models.AutoField(primary_key=True)
    target = VarcharField()
    alert = VarcharField(help_text=alert_help_text)
    clear = VarcharField(
        null=True,
        blank=True,
        help_text='The threshold for cancelling an alert. '
        'Uses same format as the threshold field',
    )
    raw = models.BooleanField(default=False)
    period = models.IntegerField(
        null=True,
        blank=True,
        help_text="Inspection interval when calculating values. "
        "For interface counters this should be set to 15 minutes",
    )
    description = VarcharField(null=True, blank=True)
    creator = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        null=True,
        related_name="treshold_rules",
    )
    created = models.DateTimeField(auto_now=True)

    class Meta(object):
        db_table = 'thresholdrule'

    def __repr__(self):
        var = [
            "{k}={v!r}".format(k=k, v=v)
            for k, v in vars(self).items()
            if not k.startswith('_') and v is not None
        ]
        return "{cls}({var})".format(cls=self.__class__.__name__, var=", ".join(var))

    def get_evaluator(self):
        """
        Returns a ThresholdEvaluator instance pre-filled with the details of
        this rule.
        """
        period = timedelta(seconds=self.period) if self.period else DEFAULT_INTERVAL
        return ThresholdEvaluator(self.target, period=period, raw=self.raw)

    def get_pattern(self):
        """
        Returns a compiled regexp pattern that represents the target metrics
        of this rule.
        """
        series = extract_series_name(self.target)
        pat = translate_serieslist_to_regex(series)
        return pat
