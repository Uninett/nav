#
# Copyright (C) 2009-2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
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
from pprint import pformat
# django already has a workaround for "no functools on py2.4"
from django.utils.functional import wraps

import django.db
from django.db import transaction

import logging
_logger = logging.getLogger(__name__)

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
        _logger.debug("Removing %d logged Django queries "
                      "(total time %.03f):\n%s",
                      query_count, runtime,
                      pformat(django.db.connection.queries))
        django.db.reset_queries()
        gc.collect()

def sum_django_queries_runtime():
    """Sums the runtime of all queries logged by django.db.connection.queries"""
    runtimes = (float(query['time'])
                for query in django.db.connection.queries)
    return sum(runtimes)

def commit_on_success(func):
    """Decorates func such that the current Django transaction is committed on
    successful return.

    If func raises an exception, the current transaction is rolled back.

    Why don't we use django.db.transaction.commit_on_success()? Because it does
    not commit or rollback unless Django actually tried to change something in
    the database. It was designed with short-lived web request cycles in mind.
    This gives us two problems:

    1. If the transaction consisted of read-only operations, the connection
       will stay idle inside a transaction, and that's bad.

    2. If a database error occurred inside a transaction, the connection would
       be useless until the transaction is rolled back.  Any further attempts
       to use the same connection will result in more errors, and a long-lived
       process will keep spewing error messages.

    """
    def _commit_on_success(*args, **kwargs):
        try:
            transaction.enter_transaction_management()
            transaction.managed(True)
            try:
                result = func(*args, **kwargs)
            except:
                transaction.rollback()
                raise
            else:
                transaction.commit()
            return result
        finally:
            transaction.leave_transaction_management()
    return wraps(func)(_commit_on_success)

def autocommit(func):
    """
    Decorates func such that Django transactions are managed to autocommitt.

    Django's autocommit decorator begins and commits a transaction on every
    statement, but will not properly rollback such a failed transaction unless
    it marked as dirty (something tried to modify the database).  This is
    because Django is optimized for a web request cycle and throws away the
    connection at the end of each request.

    """
    def _autocommit(*args, **kw):
        try:
            transaction.enter_transaction_management()
            transaction.managed(False)
            try:
                result = func(*args, **kw)
            except:
                transaction.rollback_unless_managed()
                raise
            else:
                transaction.commit_unless_managed()
                return result
        finally:
            transaction.leave_transaction_management()
    return wraps(func)(_autocommit)

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
