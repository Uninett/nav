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
"boxState event plugin"

from nav.eventengine.plugin import EventHandler

WARNING_WAIT_TIME = 20
ALERT_WAIT_TIME = 60

class BoxStateHandler(EventHandler):
    "Accepts boxState events"
    handles_types = ('boxState',)
    waiting_for_resolve = {}

    def __init__(self, *args, **kwargs):
        super(BoxStateHandler, self).__init__(*args, **kwargs)
        self.task = None

    def handle(self):
        event = self.event
        if event.state == event.STATE_START:
            return self._handle_start()
        elif event.state == event.STATE_END:
            return self._handle_end()

    def _handle_start(self):
        event = self.event
        if self._is_duplicate():
            self._logger.info(
                "%s is already down, ignoring duplicate down event",
                event.netbox)
            event.delete()
        else:
            self._logger.info("%s is not responding to ping requests; "
                              "holding possibly transient event",
                              event.netbox)
            event.netbox.up = event.netbox.UP_DOWN
            event.netbox.save()
            self.schedule(WARNING_WAIT_TIME, self._make_down_warning)

    def _handle_end(self):
        event = self.event
        if event.netbox.up == event.netbox.UP_UP:
            self._logger.info("%s is already up; ignoring up event",
                              event.netbox)
        else:
            self._logger.info("%s is back up", event.netbox)
            event.netbox.up = event.netbox.UP_UP
            event.netbox.save()
            waiter = self._get_waiting()
            if waiter:
                self._logger.info("ignoring transient down state for %s",
                                  self.event.netbox)
                waiter.deschedule()
            # TODO: post alert, update alert state
        event.delete()

    def _is_duplicate(self):
        return (self._box_already_has_down_state()
                or self._get_waiting())

    def _box_already_has_down_state(self):
        return self.event.netbox.get_unresolved_alerts('boxState').count() > 0

    def _get_waiting(self):
        return self.waiting_for_resolve.get(self.event.netbox, False)

    def _make_down_warning(self):
        self._logger.info("%s boxDownWarning not posted", self.event.netbox)
        self.task = self.engine.schedule(
            max(ALERT_WAIT_TIME-WARNING_WAIT_TIME, 0),
            self._make_down_alert)

    def _make_down_alert(self):
        self._logger.info("%s boxDown final alert not posted",
                          self.event.netbox)
        del self.waiting_for_resolve[self.event.netbox]
        self.task = None
        self.event.delete()

    def schedule(self, delay, action):
        "Schedules a callback and makes a note of it in a class variable"
        self.task = self.engine.schedule(delay, action)
        self.waiting_for_resolve[self.event.netbox] = self

    def deschedule(self):
        "Deschedules any outstanding task and deletes the associated event"
        self._logger.debug("descheduling waiting callback for %s",
                           self.event.netbox)
        self.engine.cancel(self.task)
        self.task = None
        self.event.delete()
