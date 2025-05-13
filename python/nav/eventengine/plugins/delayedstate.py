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
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
""" "Superclass for plugins that use delayed handling of state events"""

from nav.eventengine import unresolved

from nav.eventengine.topology import netbox_appears_reachable
from nav.models.manage import Netbox
from nav.eventengine.plugin import EventHandler


class DelayedStateHandler(EventHandler):
    """A plugin that wants to delay down alerts while waiting a possible
    quick resolve should be able to subclass this.

    """

    HAS_WARNING_ALERT = True
    WARNING_WAIT_TIME = 60
    ALERT_WAIT_TIME = 240

    handled_types = (None,)
    __waiting_for_resolve = {}

    def __init__(self, *args, **kwargs):
        super(DelayedStateHandler, self).__init__(*args, **kwargs)
        self.task = None
        self._set_wait_times()

    def _set_wait_times(self):
        """Sets wait times from config options under the timeouts section"""
        get_timeout_for = self.engine.config.get_timeout_for
        for wait_var in ('WARNING_WAIT_TIME', 'ALERT_WAIT_TIME'):
            new_value = get_timeout_for(getattr(self, wait_var))
            if new_value:
                setattr(self, wait_var, new_value)

    def handle(self):
        event = self.event
        if event.state == event.STATE_START:
            return self._handle_start()
        elif event.state == event.STATE_END:
            return self._handle_end()
        else:
            self._logger.info(
                "ignoring strange stateless %s event: %r", event.event_type, event
            )
            self.event.delete()

    def _handle_start(self):
        event = self.event
        if self._is_duplicate():
            self._logger.info(
                "%s is already down, ignoring duplicate start event", self.get_target()
            )
            event.delete()
        else:
            self._set_internal_state_down()
            if self.HAS_WARNING_ALERT:
                self._logger.info(
                    "%s start event for %s; warning in %s seconds, declaring "
                    "down in %s seconds (if still unresolved)",
                    self.event.event_type,
                    self.get_target(),
                    self.WARNING_WAIT_TIME,
                    self.ALERT_WAIT_TIME,
                )
                self.schedule(
                    self.WARNING_WAIT_TIME,
                    self._make_down_warning,
                    args=(self.event.get_subject(),),
                )
            else:
                self._logger.info(
                    "%s start event for %s; declaring down in %s seconds "
                    "(if still unresolved)",
                    self.event.event_type,
                    self.get_target(),
                    self.ALERT_WAIT_TIME,
                )
                self.schedule(
                    self.ALERT_WAIT_TIME,
                    self._make_down_alert,
                    args=(self.event.get_subject(),),
                )

    def _set_internal_state_down(self):
        """Called to set target's internal state to down as soon as start event
        is received.

        """
        return

    def _set_internal_state_up(self):
        """Called to set target's internal state to up as soon as end event is
        received.

        """
        return

    def _is_internally_down(self):
        """
        Called to verify whether the internal state of the target is
        currently "down".

        :return: True if down, False if upn, None if internal state cannot be
                 determined or is inapplicable for this target/event combo.
        """
        return

    def get_target(self):
        """Returns the target of the associated event"""
        raise NotImplementedError

    def _handle_end(self):
        is_unresolved = unresolved.refers_to_unresolved_alert(self.event)
        waiting_plugin = self._get_waiting()

        if is_unresolved or waiting_plugin:
            self._logger.info("%s is back up", self.get_target())
            self._set_internal_state_up()

            if is_unresolved:
                alert = self._get_up_alert()
                alert.post(post_alert=not self._box_is_on_maintenance())

            if waiting_plugin:
                self._logger.info(
                    "ignoring transient down state for %s", self.get_target()
                )
                waiting_plugin.deschedule()
        elif self._is_internally_down():
            self._logger.info(
                "no unresolved %s for %s, but its internal state "
                "was down; correcting internal state",
                self.event.event_type,
                self.get_target(),
            )
            self._set_internal_state_up()
        else:
            self._logger.info(
                "no unresolved %s for %s, ignoring end event",
                self.event.event_type,
                self.get_target(),
            )

        self.event.delete()

    def _get_up_alert(self):
        raise NotImplementedError

    def _is_duplicate(self):
        """Returns True if this appears to be a duplicate boxDown event"""
        return unresolved.refers_to_unresolved_alert(self.event) or self._get_waiting()

    def _get_waiting(self):
        """Returns a plugin instance waiting for boxState resolve
        events for the same netbox this instance is processing.

        :returns: A plugin instance, if one is waiting, otherwise False.

        """
        return self.__waiting_for_resolve.get((type(self), self.get_target()), False)

    def _make_down_warning(self, _comment=None):
        """Posts the initial boxDownWarning alert and schedules the callback
        for the final boxDown alert.

        """
        if not self._box_is_on_maintenance():
            self._post_down_warning()
        else:
            self._logger.info(
                "%s: is on maintenance, not posting warning", self.event.netbox
            )

        self.task = self.engine.schedule(
            max(self.ALERT_WAIT_TIME - self.WARNING_WAIT_TIME, 0),
            self._make_down_alert,
            args=(self.event.get_subject(),),
        )

    def _post_down_warning(self):
        """Posts the actual warning alert"""
        raise NotImplementedError

    def _make_down_alert(self, _comment=None):
        alert = self._get_down_alert()
        if alert:
            self._logger.info(
                "%s: Posting %s alert", self.get_target(), alert.alert_type
            )
            alert.post(post_alert=not self._box_is_on_maintenance())
        else:
            self._logger.error("could not find a down alert, doing nothing (%r)", alert)

        del self.__waiting_for_resolve[(type(self), self.get_target())]
        self.task = None
        self.event.delete()

    def _get_down_alert(self):
        """Returns a ready-made AlertGenerator that can be used to post a
        down alert for the implementing plugin.

        :return: An AlertGenerator instance, or None if no alert should be
                 posted.

        """
        raise NotImplementedError

    def _verify_shadow(self):
        netbox = self.event.netbox
        netbox.up = (
            Netbox.UP_DOWN if netbox_appears_reachable(netbox) else Netbox.UP_SHADOW
        )
        Netbox.objects.filter(id=netbox.id).update(up=netbox.up)
        return netbox.up == Netbox.UP_SHADOW

    def schedule(self, delay, action, args=()):
        "Schedules a callback and makes a note of it in a class variable"
        self.task = self.engine.schedule(delay, action, args=args)
        self.__waiting_for_resolve[(type(self), self.get_target())] = self

    def deschedule(self):
        """Deschedules any outstanding task and deletes the associated event"""
        self._logger.debug("descheduling waiting callback for %s", self.get_target())
        self.engine.cancel(self.task)
        self.task = None
        if self._get_waiting() == self:
            del self.__waiting_for_resolve[(type(self), self.get_target())]
        self.event.delete()
