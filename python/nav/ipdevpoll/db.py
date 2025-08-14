#
# Copyright (C) 2009-2013 Uninett AS
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
"""Database related functionality for ipdevpoll."""

import gc
import logging
from pprint import pformat
import threading
from functools import wraps
from typing import Callable, Optional

from twisted.internet import threads, reactor, abstract
from twisted.internet.base import ReactorBase
import django.db
from django.db import transaction
from django.db.utils import OperationalError as DjangoOperationalError
from django.db.utils import InterfaceError as DjangoInterfaceError
from psycopg2 import InterfaceError, OperationalError

from nav.models.event import EventQueue

_logger = logging.getLogger(__name__)
_query_logger = logging.getLogger(".".join((__name__, "query")))


class ResetDBConnectionError(Exception):
    pass


def django_debug_cleanup():
    """Resets Django's list of logged queries.

    When DJANGO_DEBUG is set to true, Django will log all generated SQL queries
    in a list, which grows indefinitely.  This is ok for short-lived processes;
    not so much for daemons.  We may want those queries in the short-term, but
    in the long-term the ever-growing list is uninteresting and also bad.

    This should be called once-in-a-while from every thread that has Django
    database access, as the queries list is stored in thread-local data.

    """
    query_count = len(django.db.connection.queries)
    if query_count:
        runtime = sum_django_queries_runtime()
        thread = threading.current_thread()
        _query_logger.debug(
            "Thread %s/%s: Removing %d logged Django queries (total time %.03f):\n%s",
            thread.ident,
            thread.name,
            query_count,
            runtime,
            pformat(django.db.connection.queries),
        )
        django.db.reset_queries()
        gc.collect()


def sum_django_queries_runtime():
    """Sums the runtime of all queries logged by django.db.connection.queries"""
    runtimes = (float(query['time']) for query in django.db.connection.queries)
    return sum(runtimes)


def cleanup_django_debug_after(func):
    """Decorates func such that django_debug_cleanup is run after func.

    Even if func raises an exception, the cleanup will be run.

    """

    def _cleanup(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            django_debug_cleanup()

    return wraps(func)(_cleanup)


def run_in_thread(func, *args, **kwargs):
    """Runs a synchronous function in a thread, with special handling of
    database errors.

    """
    return threads.deferToThread(
        reset_connection_on_interface_error(func), *args, **kwargs
    )


def reset_connection_on_interface_error(func):
    """Decorates function to reset the current thread's Django database
    connection on exceptions that appear to come from connection resets.

    """

    def _reset(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (
            InterfaceError,
            OperationalError,
            DjangoInterfaceError,
            DjangoOperationalError,
        ) as error:
            thread = threading.current_thread()
            _logger.warning(
                "it appears this thread's database connection was "
                "dropped, resetting it now - you may see further "
                "errors about this until the situation is fully "
                "resolved for all threads "
                "(this thread is '%s', function was: %r, error was '%s')",
                thread.name,
                func,
                error,
            )
            django.db.connection.connection = None
            raise ResetDBConnectionError("The database connection was reset", error)

    return wraps(func)(_reset)


def synchronous_db_access(func):
    """
    Decorates a function to run in a separate thread for synchronous database
    access
    """

    def _thread_it(*args, **kwargs):
        return run_in_thread(func, *args, **kwargs)

    return wraps(func)(_thread_it)


@transaction.atomic()
def purge_old_job_log_entries():
    """
    Purges old job log entries from the ipdevpoll_job_log db table
    """
    cursor = django.db.connection.cursor()
    # Delete all but the last 100 entries of each netbox/job_name combination,
    # ordered by timestamp
    cursor.execute(
        """
        WITH ranked AS (SELECT id, rank()
                        OVER (PARTITION BY netboxid, job_name
                              ORDER BY end_time DESC)
                        FROM ipdevpoll_job_log)
        DELETE FROM ipdevpoll_job_log USING ranked
              WHERE ipdevpoll_job_log.id = ranked.id AND rank > 100;
        """
    )


@transaction.atomic()
def delete_stale_job_refresh_notifications():
    """Deletes stale job refresh events from the database, typically at process
    startup time.

    All events in the queue can be considered stale at process startup, since all
    jobs will be re-run at startup anyway.
    """
    count, _ = EventQueue.objects.filter(target='ipdevpoll').delete()
    if count:
        _logger.info(
            "Deleted %d stale job refresh notifications from the database",
            count,
        )


def subscribe_to_event_notifications(trigger: Optional[Callable] = None):
    """Ensures the Django database connection in the calling thread is subscribed to
    'new_event' notifications from PostgreSQL.  Notification events will be read by
    an instance of PostgresNotifyReader, which is added to the Twisted reactor.

    :param trigger: An optional callable trigger function that will be called from
                    the main reactor thread whenever matching refresh notifications are
                    received.
    """

    cursor = django.db.connection.cursor()
    cursor.execute("LISTEN new_event")
    django.db.connection.commit()
    reader = PostgresNotifyReader(reactor, trigger)
    _logger.debug(
        "Subscribed to new event notifications from thread %r",
        threading.current_thread(),
    )
    reactor.addReader(reader)


def resubscribe_to_event_notifications():
    """Removes any existing PostgresNotifyReader from the reactor and adds a new one,
    re-using the trigger function of the first removed one.
    """
    trigger = _remove_postgres_reader_and_get_its_trigger_function()

    def retry_connect_loop():
        """Re-try event subscription every second, until the database connection has
        been re-established.
        """
        try:
            subscribe_to_event_notifications(trigger)
        except Exception as error:  # noqa: BLE001
            _logger.debug(
                "unable to resubscribe to events (%s), retrying in 1 second",
                str(error).strip(),
            )
            reactor.callLater(1, retry_connect_loop)

    reactor.callLater(1, retry_connect_loop)


def _remove_postgres_reader_and_get_its_trigger_function():
    postgres_readers: list[PostgresNotifyReader] = [
        reader
        for reader in reactor.getReaders()
        if isinstance(reader, PostgresNotifyReader)
    ]
    if not postgres_readers:
        return
    _logger.debug("Removing PostgresNotifyReaders: %r", postgres_readers)
    primary = postgres_readers[0]
    for reader in postgres_readers:
        reactor.removeReader(reader)

    return primary.trigger


def resubscribe_on_connection_loss(func):
    """Decorates function to re-subscribe to event notifications in the event of a
    connection loss.
    """

    def _resubscribe(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ResetDBConnectionError:
            _thread = threading.current_thread()
            _logger.debug("resubscribing to event notifications")
            resubscribe_to_event_notifications()

    return wraps(func)(_resubscribe)


class PostgresNotifyReader(abstract.FileDescriptor):
    """Implements a FileDescriptor to act on PostgreSQL notifications asynchronously.

    The LISTEN subscription is run on a random thread in the threadpool. However,
    getting the doRead code to run in the same thread as the originating connection
    is not really feasible with the API of the Twisted threadpool - so this is just
    designed to keep on trying until it's run by a thread where it succeeds.
    """

    def __init__(
        self,
        reactor: ReactorBase,
        trigger: Optional[Callable] = None,
    ):
        """Initialize a postgres notification reader.

        :param reactor: The event reactor to use for scheduling
        :param connection: The database connection object to poll for notifications
        :param trigger: A trigger function to be called from the main reactor thread
                        when a refresh  notifications is received.
        """
        self.reactor = reactor
        self.trigger = trigger
        self._fileno = django.db.connection.connection.fileno()

    def fileno(self):
        return self._fileno

    @resubscribe_on_connection_loss
    @reset_connection_on_interface_error
    def doRead(self):
        _logger.debug("PostgresNotifyReader.doRead: checking for notifications")

        connection = django.db.connection.connection
        if connection:
            _logger.debug(
                "check_for_notifications: polling for notifications from %r",
                threading.current_thread(),
            )
            connection.poll()
            if connection.notifies:
                _logger.debug("Found notifications: %r", connection.notifies)
                if any(_is_a_new_ipdevpoll_event(c) for c in connection.notifies):
                    self.schedule_trigger()
                del connection.notifies[:]
        else:
            _logger.debug(
                "check_for_notifications: connection was empty in thread %r "
                "(subscription is in %r)",
                threading.current_thread(),
            )

    def schedule_trigger(self):
        """Schedules the trigger function for an immediate run in the reactor thread"""
        if not self.trigger:
            return
        _logger.debug(
            "scheduling %r to be called from main reactor thread", self.trigger
        )
        self.reactor.callInThread(self.trigger)


def _is_a_new_ipdevpoll_event(notification):
    return notification.channel == "new_event" and notification.payload == "ipdevpoll"
