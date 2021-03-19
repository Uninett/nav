#
# Copyright (C) 2012 Uninett AS
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
"""servicestate handler plugin"""

from nav.eventengine.plugin import EventHandler
from nav.eventengine.alerts import AlertGenerator
from nav.models.event import EventQueue as Event
from nav.models.manage import Netbox
from nav.models.service import Service


class ServiceStateHandler(EventHandler):
    """Accepts serviceState events"""

    handled_types = ('serviceState',)

    def handle(self):
        event = self.event
        alert = AlertGenerator(event)

        if event.state in [event.STATE_START, event.STATE_END]:
            service = self._update_service()
            self._set_alert_type(alert, service)

        self._populate_alert(alert)

        alert.post(post_alert=not self._box_is_on_maintenance())

        event.delete()

    def _update_service(self):
        """Update state of service directly based on event"""
        event = self.event
        service = Service.objects.get(pk=event.subid)
        service.up = (
            Service.UP_DOWN if event.state == Event.STATE_START else Service.UP_UP
        )
        service.save()
        return service

    @staticmethod
    def _set_alert_type(alert, service):
        """Set alerttype based on handler and event state"""
        state = 'Down' if alert.state == Event.STATE_START else 'Up'
        alert.alert_type = service.handler + state

    def _populate_alert(self, alert):
        """Populate alert-dict with variables used in alertmessage"""
        alert['deviceup'] = 'Yes' if self.event.netbox.up == Netbox.UP_UP else 'No'
        try:
            service = Service.objects.get(pk=self.event.subid)
            alert['service'] = service
        except Service.DoesNotExist:
            pass
