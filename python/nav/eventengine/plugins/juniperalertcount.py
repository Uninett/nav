#
# Copyright (C) 2022 Sikt
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
"""juniper alert count handler plugin"""

from nav.eventengine import unresolved
from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.plugin import EventHandler
from nav.models.event import STATE_CHOICES


class JuniperAlertCountHandler(EventHandler):
    """Accepts juniperYellowAlarmState and juniperRedAlarmState events"""

    handled_types = (
        'juniperYellowAlarmState',
        'juniperRedAlarmState',
    )

    def handle(self):
        event = self.event

        if event.state == event.STATE_STATELESS:
            self._logger.warning(
                'Ignoring stateless %s event: %r', event.event_type, event
            )
            self.event.delete()
        elif event.state == event.STATE_START:
            return self._handle_start()
        elif event.state == event.STATE_END:
            return self._handle_end()

    def _handle_start(self):
        event = self.event
        alert = AlertGenerator(event)

        if self._delete_event_with_incorrect_alert_type(
            event=event,
            alert_type=alert.alert_type,
            accepted_alert_types=["juniperRedAlarmOn", "juniperYellowAlarmOn"],
        ):
            return

        alert.history_vars = {"count": alert["count"]}
        unresolved_alert = unresolved.refers_to_unresolved_alert(self.event)

        if unresolved_alert:
            if int(alert["count"]) == int(
                unresolved_alert.variables.get(variable="count").value
            ):
                self._logger.warning(
                    'Ignoring duplicate %s start event: %r',
                    event.event_type,
                    event,
                )
                event.delete()
                return

            unresolved_alert.end_time = event.time
            unresolved_alert.save()

        alert.post()
        event.delete()

    def _handle_end(self):
        event = self.event
        alert = AlertGenerator(event)

        if self._delete_event_with_incorrect_alert_type(
            event=event,
            alert_type=alert.alert_type,
            accepted_alert_types=["juniperRedAlarmOff", "juniperYellowAlarmOff"],
        ):
            return

        unresolved_alert = unresolved.refers_to_unresolved_alert(event)

        if unresolved_alert:
            alert.post()
        else:
            self._logger.warning(
                "no unresolved %s for %s, ignoring end event",
                self.event.event_type,
                self.get_target(),
            )

        self.event.delete()

    def get_target(self):
        return self.event.get_subject()

    def _delete_event_with_incorrect_alert_type(
        self, event, alert_type, accepted_alert_types
    ):
        """
        Checks if an the alert type of an event is within the given accepted alert
        types and deletes the event and returns true if not
        """
        if alert_type not in accepted_alert_types:
            self._logger.warning(
                'Ignoring %s %s event with alert type %s: %r',
                event.event_type,
                dict(STATE_CHOICES)[event.state],
                alert_type,
                event,
            )
            event.delete()
            return True

        return False
