#
# Copyright (C) 2012 UNINETT
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
"""Alert generator functionality for the eventEngine"""
import datetime
from nav.models.event import AlertQueue as Alert, AlertHistory

INFINITY = datetime.datetime.max

class AlertGenerator(object):
    def __init__(self, event):
        self.event = event
        self.alert = self._generateAlert()
        self.history = self._generateAlertHistory()

    def _generateAlert(self):
        attrs = {}
        for attr in ('source', 'device', 'netbox', 'subid', 'time',
                     'event_type', 'state', 'value', 'severity'):
            attrs[attr] = getattr(self.event, attr)
        alert = Alert(**attrs)
        alert.varmap = self.event.varmap
        return alert

    def _generateAlertHistory(self):
        if self.event.state == self.event.STATE_END:
            return None

        attrs = dict(
            start_time=self.event.time,
            end_time=INFINITY if self.event.state == self.event.STATE_START
            else None)
        for attr in ('source', 'device', 'netbox', 'subid', 'event_type',
                     'value', 'severity'):
            attrs[attr] = getattr(self.event, attr)
        alert = AlertHistory(**attrs)
        alert.varmap = self.event.varmap
        return alert

    def is_event_duplicate(self):
        """Returns True if the represented event seems to duplicate an
        existing unresolved alert.

        """
        unresolved = get_unresolved_alerts_map()
        return (self.event.state == self.event.STATE_START
                and self.event.get_key() in unresolved)

def get_unresolved_alerts_map():
    """Returns a dictionary of unresolved AlertHistory entries"""
    unresolved = AlertHistory.objects.filter(end_time__gte=INFINITY)
    return dict((alert.get_key(), alert) for alert in unresolved)
