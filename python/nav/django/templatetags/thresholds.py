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
"""Template tags for discovering threshold rules related to metric names"""

from django import template
from nav.models.thresholds import ThresholdRule


register = template.Library()


@register.filter
def find_rules(metrics):
    """
    Finds threshold rules that match the metrics mentioned in the metrics
    list.

    :param metrics: A list of modifiable dict() objects that each must at
                    least contain the key 'id', which should refer to a metric
                    id.
    :type metrics: list(dict(), ...)
    :return: The modified metrics list, with each dict() object having a
             thresholds key added.

    """
    rules = [(r.get_pattern(), r) for r in ThresholdRule.objects.all()]
    for metric in metrics:
        thresholds = metric.setdefault('thresholds', [])
        for pat, rule in rules:
            if pat.match(metric['id']):
                thresholds.append(rule)
    return metrics


@register.filter
def find_thresholds(metric):
    """Finds the threshold set for this metric"""
    rules = [(r.get_pattern(), r) for r in ThresholdRule.objects.all()]
    thresholds = [rule for pat, rule in rules if pat.match(metric)]
    return ",".join([t.alert for t in thresholds])
