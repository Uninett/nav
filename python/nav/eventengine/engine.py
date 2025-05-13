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
"""The actual "engine" part of the NAV eventEngine

Will check the eventq ever so often, but will also react to notifications from
PostgreSQL. To add notification of new events posted to eventq, the following
SQL is needed::

    CREATE RULE eventq_notify AS ON INSERT TO eventq DO ALSO NOTIFY new_event;

"""

import logging
import sched
import select
import time
from functools import wraps
import errno

from psycopg2 import OperationalError
from django.db import connection, DatabaseError, transaction

from nav.eventengine import export
from nav.eventengine.plugin import EventHandler
from nav.eventengine.alerts import AlertGenerator
from nav.eventengine.config import EVENTENGINE_CONF
from nav.eventengine import unresolved
from nav.eventengine.severity import SeverityRules
from nav.models.event import EventQueue as Event
import nav.db

_logger = logging.getLogger(__name__)


def harakiri():
    """Kills the entire daemon when no database is available"""
    _logger.fatal("unable to establish database connection, qutting...")
    raise SystemExit(1)


def retry_on_db_loss():
    """Returns a nav.db.retry_on_db_loss decorator with eventengine's default
    parameters.
    """
    return nav.db.retry_on_db_loss(
        count=3, delay=5, fallback=harakiri, also_handled=(DatabaseError,)
    )


def swallow_unhandled_exceptions(func):
    """Decorates a function to log and ignore any exceptions thrown by it
    :param func: The function to decorate
    :return: A decorated version of func

    """

    @wraps(func)
    def _decorated(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:  # noqa: BLE001
            _logger.exception("Unhandled exception occurred; ignoring it")

    return _decorated


class EventEngine(object):
    """Event processing engine.

    Only one instance of this class should ever be needed.

    """

    # interval for regularly scheduled queue checks. these don't need to be
    # too often, since we rely on PostgreSQL notification when new events are
    # inserted into the queue.
    CHECK_INTERVAL = 30
    PLUGIN_TASKS_PRIORITY = 1
    _logger = logging.getLogger(__name__)

    def __init__(self, target="eventEngine", config=EVENTENGINE_CONF):
        self._scheduler = sched.scheduler(time.time, self._notifysleep)
        self._unfinished = set()
        self.target = target
        self.config = config
        self.handlers = EventHandler.load_and_find_subclasses()
        self._logger.debug(
            "found %d event handler%s: %r",
            len(self.handlers),
            's' if len(self.handlers) > 1 else '',
            self.handlers,
        )

    def _notifysleep(self, delay):
        """Sleeps up to delay number of seconds, but will schedule an
        immediate new event queue check if an event notification is received
        from PostgreSQL.

        """
        conn = connection.connection
        if conn:
            self._logger.debug("select sleep for %ss", delay)
            try:
                select.select([conn], [], [], delay)
            except select.error as err:
                if err.args[0] != errno.EINTR:
                    raise
            try:
                conn.poll()
            except OperationalError:
                connection.connection = None
                self._listen()
                return
            if conn.notifies:
                self._logger.debug("got event notification from database")
                self._schedule_next_queuecheck()
                del conn.notifies[:]
        else:
            self._logger.debug("regular sleep for %ss", delay)
            time.sleep(delay)

    def start(self):
        "Starts the event engine"
        self._logger.info("--- starting event engine ---")
        self._load_severity_rules()
        self._start_export_script()
        self._listen()
        self._load_new_events_and_reschedule()
        self._scheduler.run()
        self._logger.debug("scheduler exited")

    @staticmethod
    def _load_severity_rules():
        # Imbues the AlertGenerator class with user-defined severity rules
        AlertGenerator.severity_rules = SeverityRules.load_from_file()

    def _start_export_script(self):
        if self.config.has_option("export", "script"):
            script = self.config.get("export", "script")
            self._logger.info("Starting export script: %r", script)
            try:
                export.exporter = export.StreamExporter(script)
            except OSError as error:
                self._logger.error("Cannot start export script: %s", error)
        else:
            export.exporter = None

    @staticmethod
    @retry_on_db_loss()
    @transaction.atomic()
    def _listen():
        """Ensures that we subscribe to new_event notifications on our
        PostgreSQL connection.

        """
        _logger.debug("registering event listener with PostgreSQL")
        cursor = connection.cursor()
        cursor.execute('LISTEN new_event')

    def _load_new_events_and_reschedule(self):
        self.load_new_events()
        self._schedule_next_queuecheck(
            self.CHECK_INTERVAL, action=self._load_new_events_and_reschedule
        )

    def _schedule_next_queuecheck(self, delay=0, action=None):
        if not action:
            action = self.load_new_events

        self._scheduler.enter(delay, 0, action, ())

    @swallow_unhandled_exceptions
    @transaction.atomic()
    def load_new_events(self):
        "Loads and processes new events on the queue, if any"
        self._logger.debug("checking for new events on queue")
        events = Event.objects.filter(target=self.target).order_by('id')
        if events:
            old_events = [event for event in events if event.id in self._unfinished]
            new_events = [event for event in events if event.id not in self._unfinished]
            self._logger.info(
                "found %d new and %d old events in queue db",
                len(new_events),
                len(old_events),
            )
            for event in new_events:
                unresolved.update()
                try:
                    self.handle_event(event)
                except Exception:  # noqa: BLE001
                    self._logger.exception(
                        "Unhandled exception while handling %s, deleting event",
                        event,
                    )
                    if event.id:
                        event.delete()

        self._log_task_queue()

    def _log_task_queue(self):
        _logger = logging.getLogger(__name__ + '.queue')
        _logger.debug("about to log task queue: %d", len(self._scheduler.queue))
        if not _logger.isEnabledFor(logging.DEBUG):
            return

        modified_queue = [
            e
            for e in self._scheduler.queue
            if e.action != self._load_new_events_and_reschedule
        ]
        if modified_queue:
            logtime = time.time()
            _logger.debug("%d tasks in queue at %s", len(modified_queue), logtime)
            for event in modified_queue:
                _logger.debug("In %s seconds: %r", event.time - logtime, event)

    def _post_generic_alert(self, event):
        alert = AlertGenerator(event)
        if 'alerttype' in event.varmap:
            alert.alert_type = event.varmap['alerttype']

        is_stateless = event.state == Event.STATE_STATELESS
        if is_stateless or not alert.is_event_duplicate():
            if self._box_is_on_maintenance(event):
                self._logger.debug(
                    '%s is on maintenance, only posting to alert history for %s event',
                    event.netbox,
                    event.event_type,
                )
                alert.post(post_alert=False)
            else:
                self._logger.debug('Posting %s event', event.event_type)
                alert.post()
        else:
            self._logger.info(
                'Ignoring duplicate %s event for %s', event.event_type, event.netbox
            )
            self._logger.debug('ignored alert details: %r', event)
        event.delete()

    @staticmethod
    def _box_is_on_maintenance(event):
        """Returns True if the event's associated netbox is currently on
        maintenance.
        """
        return (
            event.netbox
            and event.netbox.get_unresolved_alerts('maintenanceState').count() > 0
        )

    @transaction.atomic()
    def handle_event(self, event):
        "Handles a single event"
        original_id = event.id

        self._logger.debug("handling %r", event)
        queue = [cls(event, self) for cls in self.handlers if cls.can_handle(event)]
        self._logger.debug("plugins that can handle: %r", queue)
        if not queue:
            self._post_generic_alert(event)

        for handler in queue:
            self._logger.debug("giving event to %s", handler.__class__.__name__)
            try:
                handler.handle()
            except Exception:  # noqa: BLE001
                self._logger.exception(
                    "Unhandled exception in plugin %s; ignoring it", handler
                )
                if len(queue) == 1 and event.id:
                    # there's only one handler and it failed,
                    # this will probably never be handled, so we delete it
                    event.delete()

        if event.id:
            self._logger.debug(
                "event wasn't disposed of, maybe held for later processing? %r",
                event,
            )
            self._unfinished.add(event.id)
        elif original_id in self._unfinished:
            self._unfinished.remove(original_id)

    def schedule(self, delay, action, args=()):
        """Schedule running action after a given delay"""
        self._logger.debug(
            "scheduling delayed task in %s seconds: %r (args=%r)", delay, action, args
        )
        return self._scheduler.enter(
            delay,
            self.PLUGIN_TASKS_PRIORITY,
            swallow_unhandled_exceptions(action),
            args,
        )

    def cancel(self, task):
        """Cancel the current scheduled task"""
        self._scheduler.cancel(task)
