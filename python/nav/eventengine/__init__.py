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
"""new event engine prototype.

will check the eventq ever so often, but will also react to notifications from
PostgreSQL.  to add notification of new events posted to eventq, the following
sql is needed:

CREATE RULE eventq_notify AS ON INSERT TO eventq DO ALSO NOTIFY new_event;

"""
import time
import sched
import select
import logging

from nav.models.event import EventQueue as Event
from django.db import connection
from nav.ipdevpoll.db import commit_on_success
from nav.eventengine.plugin import EventHandler

class EventEngine(object):
    """Event processing engine.

    Only one instance of this class should ever be needed.

    """
    # interval for regularly scheduled queue checks. these don't need to be
    # too often, since we rely on PostgreSQL notification when new events are
    # inserted into the queue.
    CHECK_INTERVAL = 30
    _logger = logging.getLogger(__name__)

    def __init__(self, target="eventEngine"):
        self._scheduler = sched.scheduler(time.time, self._notifysleep)
        self.target = target
        self.last_event_id = 0
        self.handlers = EventHandler.load_and_find_subclasses()
        self._logger.debug("found %d event handler%s: %r",
                           len(self.handlers),
                           's' if len(self.handlers) > 1 else '',
                           self.handlers)

    def _notifysleep(self, delay):
        """Sleeps up to delay number of seconds, but will schedule an
        immediate new event queue check if an event notification is received
        from PostgreSQL.

        """
        conn = connection.connection
        if conn:
            select.select([conn], [], [], delay)
            conn.poll()
            if conn.notifies:
                self._logger.debug("got event notification from database")
                self._schedule_next_queuecheck()
                del conn.notifies[:]
        else:
            time.sleep(delay)

    def start(self):
        "Starts the event engine"
        self._logger.info("--- starting event engine ---")
        self._listen()
        self._load_new_events_and_reschedule()
        self._scheduler.run()

    @staticmethod
    @commit_on_success
    def _listen():
        """Ensures that we subscribe to new_event notifications on our
        PostgreSQL connection.

        """
        cursor = connection.cursor()
        cursor.execute('LISTEN new_event')

    def _load_new_events_and_reschedule(self):
        self.load_new_events()
        self._schedule_next_queuecheck(
            self.CHECK_INTERVAL,
            action=self._load_new_events_and_reschedule)

    def _schedule_next_queuecheck(self, delay=0, action=None):
        if not action:
            action = self.load_new_events

        self._scheduler.enter(delay, 0, action, ())

    @commit_on_success
    def load_new_events(self):
        "Loads and processes new events on the queue, if any"
        self._logger.debug("checking for new events on queue")
        events = Event.objects.filter(
            target=self.target, id__gt=self.last_event_id
            ).order_by('id')
        if events:
            events = list(events)
            self._logger.info("found %d new events in queue db", len(events))
            self.last_event_id = events[-1].id
            for event in events:
                self.handle_event(event)

    def handle_event(self, event):
        "Handles a single event"
        self._logger.debug("handling %r", event)
        queue = [cls(event) for cls in self.handlers
                 if cls.can_handle(event)]
        for handler in queue:
            self._logger.debug("giving event to %s", handler.__class__.__name__)
            result = handler.handle()

        if event.id:
            self._logger.debug("event wasn't disposed of, "
                               "maybe held for later processing?")
