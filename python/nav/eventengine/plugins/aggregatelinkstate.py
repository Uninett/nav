#
# Copyright (C) 2016 Uninett AS
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
from nav.eventengine import unresolved
from nav.eventengine.plugin import EventHandler
from nav.eventengine.alerts import AlertGenerator


class AggregateLinkStateHandler(EventHandler):
    """Accepts aggregateLinkState events"""
    handled_types = ('aggregateLinkState',)

    def handle(self):
        event = self.event
        alert = AlertGenerator(event)
        interface = event.get_subject()
        is_unresolved = unresolved.refers_to_unresolved_alert(event)

        if event.state == event.STATE_START:
            alert.alert_type = 'linkDegraded'
            if is_unresolved:
                return self._handle_duplicate(alert, is_unresolved)
            if not interface.is_degraded():
                return self._ignore("Got aggregateLinkState start event, but "
                                    "the interface is not currently degraded.")

        elif event.state == event.STATE_END:
            alert.alert_type = 'linkRestored'
            if not is_unresolved:
                return self._ignore("Got aggregateLinkState end event, but "
                                    "there is no currently active alert to "
                                    "resolve.")
            if interface.is_degraded():
                return self._ignore("Got aggregateLinkState end event, but the "
                                    "interface still appears to be degraded.")

        if self._box_is_on_maintenance():
            alert.post_alert_history()
        else:
            alert.post()

        event.delete()

    def _handle_duplicate(self, alert, existing_alert):
        interface = self.event.get_subject()
        self._logger.info("%s: Got another linkDegraded event, interface is "
                          "possibly degraded further", interface)
        self._logger.debug("%s: The unresolved AlertHist entry is %r",
                           interface, vars(existing_alert))
        # Post just an alertq entry, but don't touch alerthist
        alert.post_alert(history=existing_alert)
        self.event.delete()

    def _ignore(self, msg):
        interface = self.event.get_subject()
        self._logger.info("%s: %s Ignoring event.", interface, msg)
        self.event.delete()
