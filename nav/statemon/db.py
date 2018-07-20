#
# Copyright (C) 2010, 2012 Uninett AS
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
"""
This class is an abstraction of the database operations needed
by the service monitor.

It implements the singleton pattern, ensuring only one instance
is used at a time.
"""
from __future__ import absolute_import

import threading
try:
    import queue
except ImportError:
    import Queue as queue
import time
import atexit
from collections import defaultdict
import logging

import psycopg2
from psycopg2.errorcodes import IN_FAILED_SQL_TRANSACTION
from psycopg2.errorcodes import lookup as pg_err_lookup

from nav.db import get_connection_string
from nav.util import synchronized

from . import checkermap
from .event import Event


LOGGER = logging.getLogger(__name__)


def db():
    """Returns a db singleton"""
    if getattr(_DB, '_instance') is None:
        setattr(_DB, '_instance', _DB())

    return getattr(_DB, '_instance')


class DbError(Exception):
    """Generic database error"""


_queryLock = threading.Lock()


class _DB(threading.Thread):
    _instance = None

    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self.queue = queue.Queue()
        self._hosts_to_ping = []
        self._checkers = []
        self.db = None

    def connect(self):
        """Connects to the NAV database"""
        try:
            conn_str = get_connection_string(script_name='servicemon')
            self.db = psycopg2.connect(conn_str)
            atexit.register(self.close)

            LOGGER.info("Successfully (re)connected to NAVdb")
            # Set transaction isolation level to READ COMMITTED
            self.db.set_isolation_level(1)
        except Exception:
            LOGGER.critical("Couldn't connect to db.", exc_info=True)
            self.db = None

    def close(self):
        """Closes the database connection"""
        try:
            if self.db:
                self.db.close()
        except psycopg2.InterfaceError:
            # ignore "already-closed" type errors
            pass

    def status(self):
        """Returns 0/1 connection status indicator"""
        try:
            if self.db.status:
                return 1
        except Exception:
            return 0
        return 0

    def cursor(self):
        """
        Returns a database cursor, automatically re-opening the database
        connection if necessary.

        """
        try:
            try:
                cursor = self.db.cursor()
                cursor.execute('SELECT 1')
            except psycopg2.InternalError as err:
                if err.pgcode == IN_FAILED_SQL_TRANSACTION:
                    LOGGER.critical("Rolling back aborted transaction...")
                    self.db.rollback()
                else:
                    LOGGER.critical("PostgreSQL reported an internal error "
                                    "I don't know how to handle: %s "
                                    "(code=%s)", pg_err_lookup(err.pgcode),
                                    err.pgcode)
                    raise
        except Exception as err:
            if self.db is not None:
                LOGGER.critical("Could not get cursor. Trying to reconnect...",
                                exc_info=True)
            self.close()
            self.connect()
            cursor = self.db.cursor()
        return cursor

    def run(self):
        """Runs the event posting loop, popping events from the queue"""
        self.connect()
        while 1:
            event = self.queue.get()
            LOGGER.debug("Got event: [%s]", event)
            try:
                self.commit_event(event)
                self.db.commit()
            except Exception:
                # If we fail to commit the event, place it
                # back in our queue
                LOGGER.debug("Failed to commit event, rescheduling...")
                self.new_event(event)
                time.sleep(5)

    @synchronized(_queryLock)
    def query(self, statement, values=None, commit=1):
        """
        Runs a synchronized database query, automatically re-opening a
        troubled connection and handling errors.

        """
        cursor = None
        try:
            cursor = self.cursor()
            cursor.execute(statement, values)
            LOGGER.debug("Executed: %s", cursor.query)
            if commit:
                self.db.commit()
            return cursor.fetchall()
        except Exception:
            LOGGER.critical("Failed to execute query: %s",
                            cursor.query if cursor else statement,
                            exc_info=True)
            if commit:
                try:
                    self.db.rollback()
                except Exception:
                    LOGGER.critical("Failed to rollback")
            raise DbError()

    @synchronized(_queryLock)
    def execute(self, statement, values=None, commit=1):
        """
        Runs a synchronized database query, ignoring any result rows.
        Automatically re-opens a troubled connection, and handles errors.

        """
        cursor = None
        try:
            cursor = self.cursor()
            cursor.execute(statement, values)
            LOGGER.debug("Executed: %s", cursor.query)
            if commit:
                try:
                    self.db.commit()
                except Exception:
                    LOGGER.critical("Failed to commit")
        except psycopg2.IntegrityError:
            LOGGER.critical("Database integrity error, throwing away update",
                            exc_info=True)
            LOGGER.debug("Tried to execute: %s", cursor.query)
            if commit:
                self.db.rollback()
        except Exception:
            LOGGER.critical("Could not execute statement: %s",
                            cursor.query if cursor else statement,
                            exc_info=True)
            if commit:
                self.db.rollback()
            raise DbError()

    def new_event(self, event):
        """Places a new event on the queue to be posted to the db"""
        self.queue.put(event)

    def commit_event(self, event):
        """Commits an event to the database event queue"""
        if event.source not in ("serviceping", "pping"):
            LOGGER.critical("Invalid source for event: %s", event.source)
            return
        if event.eventtype == "version":
            statement = """UPDATE service SET version = %s
                           WHERE serviceid = %s"""
            self.execute(statement, (event.version, event.serviceid))
            return

        if event.status == Event.UP:
            value = 100
            state = 'e'
        elif event.status == Event.DOWN:
            value = 1
            state = 's'
        else:
            value = 1
            state = 'x'

        nextid = self.query("SELECT nextval('eventq_eventqid_seq')")[0][0]
        statement = """INSERT INTO eventq
                       (eventqid, subid, netboxid, eventtypeid,
                        state, value, source, target)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (nextid, event.serviceid, event.netboxid,
                  event.eventtype, state, value, event.source, "eventEngine")
        self.execute(statement, values)

        statement = """INSERT INTO eventqvar
                       (eventqid, var, val) VALUES
                       (%s, %s, %s)"""
        values = (nextid, 'descr', event.info)
        self.execute(statement, values)

    def hosts_to_ping(self):
        """Returns a list of netboxes to ping, from the database"""
        query = """SELECT netboxid, sysname, ip, up FROM netbox """
        try:
            self._hosts_to_ping = self.query(query)
        except DbError:
            return self._hosts_to_ping
        return self._hosts_to_ping

    def get_checkers(self, use_db_status, onlyactive=1):
        """
        Returns a list of service checker instances based on the database
        service handler registry.

        """
        query = """SELECT serviceid, property, value
        FROM serviceproperty
        order BY serviceid"""

        properties = defaultdict(dict)
        try:
            dbprops = self.query(query)
        except DbError:
            return self._checkers
        for serviceid, prop, value in dbprops:
            if value:
                properties[serviceid][prop] = value

        query = """SELECT serviceid ,service.netboxid,
        service.active, handler, version, ip, sysname, service.up
        FROM service JOIN netbox ON
        (service.netboxid=netbox.netboxid) order by serviceid"""
        try:
            fromdb = self.query(query)
        except DbError:
            return self._checkers

        self._checkers = []
        for (serviceid, netboxid, active, handler, version, ip,
             sysname, upstate) in fromdb:
            checker = checkermap.get(handler)
            if not checker:
                LOGGER.critical("no such checker: %s", handler)
                continue
            service = {
                'id': serviceid,
                'netboxid': netboxid,
                'ip': ip,
                'sysname': sysname,
                'args': properties[serviceid],
                'version': version
                }

            kwargs = {}
            if use_db_status:
                if upstate == 'y':
                    upstate = Event.UP
                else:
                    upstate = Event.DOWN
                kwargs['status'] = upstate

            try:
                new_checker = checker(service, **kwargs)
            except Exception:
                LOGGER.critical("Checker %s (%s) failed to init. This checker "
                                "will remain DISABLED:",  handler, checker,
                                exc_info=True)
                continue

            if onlyactive and not active:
                continue
            else:
                setattr(new_checker, 'active', active)

            self._checkers += [new_checker]
        LOGGER.info("Returned %s checkers", len(self._checkers))
        return self._checkers
