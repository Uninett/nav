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
from nav.models.event import AlertQueue as Alert, EventQueue as Event, AlertType
from nav.models.event import AlertHistory

INFINITY = datetime.datetime.max

class AlertGenerator(dict):
    def __init__(self, event):
        super(AlertGenerator, self).__init__()
        self.event = event

        self.source = event.source
        self.device = event.device
        self.netbox = event.netbox
        self.subid = event.subid
        self.time = event.time
        self.event_type = event.event_type
        self.state = event.state
        self.value = event.value
        self.severity = event.severity

        self.update(event.varmap)

        if 'alert_type' in self:
            self.alert_type = self['alert_type']
            del self['alert_type']
        else:
            self.alert_type = None

    def make_alert(self):
        """Generates an alert object based on the current attributes"""
        attrs = {}
        for attr in ('source', 'device', 'netbox', 'subid', 'time',
                     'event_type', 'state', 'value', 'severity'):
            attrs[attr] = getattr(self, attr)
        alert = Alert(**attrs)
        alert.alert_type = self.get_alert_type()
        alert.varmap = self
        return alert

    def make_alert_history(self):
        """Generates an alert history object based on the current attributes"""
        if self.state == Event.STATE_END:
            return None

        attrs = dict(
            start_time=self.time,
            end_time=INFINITY if self.state == Event.STATE_START
            else None)
        for attr in ('source', 'device', 'netbox', 'subid', 'event_type',
                     'value', 'severity'):
            attrs[attr] = getattr(self, attr)
        alert = AlertHistory(**attrs)
        alert.alert_type = self.get_alert_type()
        alert.varmap = self
        return alert

    def post(self):
        """Generates and posts the necessary alert objects to the database"""
        self.post_alert_history()
        self.post_alert()

    def post_alert(self):
        """Generates and posts an alert on the alert queue only"""
        alert = self.make_alert()
        alert.save()

    def post_alert_history(self):
        """Generates and posts an alert history record only"""
        history = self.make_alert_history()
        history.save()

    def is_event_duplicate(self):
        """Returns True if the represented event seems to duplicate an
        existing unresolved alert.

        """
        unresolved = get_unresolved_alerts_map()
        return (self.event.state == Event.STATE_START
                and self.event.get_key() in unresolved)

    def get_alert_type(self):
        return AlertType.objects.get(name=self.alert_type)

def get_unresolved_alerts_map():
    """Returns a dictionary of unresolved AlertHistory entries"""
    unresolved = AlertHistory.objects.filter(end_time__gte=INFINITY)
    return dict((alert.get_key(), alert) for alert in unresolved)
