#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Metric threshold related models"""
from django.db import models
from nav.models.profiles import Account
from nav.models.fields import VarcharField
from nav.metrics.thresholds import ThresholdEvaluator, DEFAULT_INTERVAL


class ThresholdRule(models.Model):
    """A threshold rule"""
    id = models.AutoField(primary_key=True)
    target = VarcharField()
    alert = VarcharField()
    clear = VarcharField(null=True, blank=True)
    raw = models.BooleanField(default=False)
    period = VarcharField(null=True, blank=True)
    description = VarcharField(null=True, blank=True)
    creator = models.ForeignKey(Account, null=True)
    created = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'thresholdrule'

    def __repr__(self):
        var = ["{k}={v!r}".format(k=k, v=v)
               for k, v in vars(self).items()
               if not k.startswith('_') and v is not None]
        return "{cls}({var})".format(cls=self.__class__.__name__,
                                     var=", ".join(var))

    def get_evaluator(self):
        return ThresholdEvaluator(self.target,
                                  period=self.period or DEFAULT_INTERVAL,
                                  raw=self.raw)
