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

from twisted.internet import threads
import django.db
from django.db import transaction
from django.db.utils import OperationalError as DjangoOperationalError
from django.db.utils import InterfaceError as DjangoInterfaceError
from psycopg2 import InterfaceError, OperationalError

_logger = logging.getLogger(__name__)


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
        _logger.debug(
            "Thread %s/%s: Removing %d logged Django queries "
            "(total time %.03f):\n%s",
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
                "(this thread is '%s', error was '%s')",
                thread.name,
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
