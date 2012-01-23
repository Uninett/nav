#
# Copyright (C) 2002 Norwegian University of Science and Technology
# Copyright (C) 2010, 2012 UNINETT AS
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
import os
import threading
import checkermap
import psycopg2
from psycopg2.errorcodes import IN_FAILED_SQL_TRANSACTION
from psycopg2.errorcodes import lookup as pg_err_lookup
import Queue
import time
import atexit
import traceback
from functools import wraps

from event import Event
from service import Service
from debug import debug

from nav.db import get_connection_string

def synchronized(lock):
    """Synchronization decorator.

    Since there is only one database connection, we need to serialize access
    to it so multiple threads won't interfere with each others transactions.

    """
    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            lock.acquire()
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()
        return _wrapper
    return _decorator

def db():
    if _db._instance is None:
        _db._instance = _db()

    return _db._instance

class dbError(Exception):
    pass

class UnknownRRDFileError(Exception):
    pass

_queryLock = threading.Lock()
class _db(threading.Thread):
    _instance = None
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(1)
        self.queue = Queue.Queue()
        self._hostsToPing = []
        self._checkers = []
        self.db = None

    def connect(self):
        try:
            conn_str = get_connection_string(script_name='servicemon')
            self.db = psycopg2.connect(conn_str)
            atexit.register(self.close)

            debug("Successfully (re)connected to NAVdb")
            # Set transaction isolation level to READ COMMITTED
            self.db.set_isolation_level(1)
        except Exception, e:
            debug("Couldn't connect to db.", 2)
            debug(str(e), 2)
            self.db = None

    def close(self):
        try:
            if self.db:
                self.db.close()
        except psycopg2.InterfaceError:
            # ignore "already-closed" type errors
            pass

    def status(self):
        try:
            if self.db.status:
                return 1
        except:
            return 0
        return 0

    def cursor(self):
        try:
            try:
                cursor = self.db.cursor()
                cursor.execute('SELECT 1')
            except psycopg2.InternalError, err:
                if err.pgcode == IN_FAILED_SQL_TRANSACTION:
                    debug("Rolling back aborted transaction...", 2)
                    self.db.rollback()
                else:
                    debug("PostgreSQL reported an internal error I don't know "
                          "how to handle: %s (code=%s)" % (
                            pg_err_lookup(err.pgcode), err.pgcode), 2)
                    raise
        except Exception, err:
            debug(str(err), 2)
            debug("Could not get cursor. Trying to reconnect...", 2)
            self.close()
            self.connect()
            cursor = self.db.cursor()
        return cursor

    def run(self):
        self.connect()
        while 1:
            event = self.queue.get()
            debug("Got event: [%s]" % event, 7)
            try:
                self.commitEvent(event)
                self.db.commit()
            except Exception, e:
                # If we fail to commit the event, place it
                # back in our queue
                debug("Failed to commit event, rescheduling...", 7)
                self.newEvent(event)
                time.sleep(5)

    @synchronized(_queryLock)
    def query(self, statement, values=None, commit=1):
        cursor = None
        try:
            cursor = self.cursor()
            cursor.execute(statement, values)
            debug("Executed: %s" % cursor.query, 7)
            if commit:
                self.db.commit()
            return cursor.fetchall()
        except Exception, e:
            debug("Failed to execute query: "
                  "%s" % cursor.query if cursor else statement, 2)
            debug(str(e))
            if commit:
                try:
                    self.db.rollback()
                except Exception:
                    debug("Failed to rollback", 2)
            raise dbError()

    @synchronized(_queryLock)
    def execute(self, statement, values=None, commit=1):
        cursor = None
        try:
            cursor = self.cursor()
            cursor.execute(statement, values)
            debug("Executed: %s" % cursor.query, 7)
            if commit:
                try:
                    self.db.commit()
                except:
                    debug("Failed to commit", 2)
        except psycopg2.IntegrityError, e:
            debug(str(e), 2)
            debug("Tried to execute: %s" % cursor.query, 7)
            debug("Throwing away update...", 2)
            if commit:
                self.db.rollback()
        except Exception, e:
            debug("Could not execute statement: "
                  "%s" % cursor.query if cursor else statement, 2)
            debug(str(e))
            if commit:
                self.db.rollback()
            raise dbError()

    def newEvent(self, event):
        self.queue.put(event)

    def commitEvent(self, event):
        if event.source not in ("serviceping","pping"):
            debug("Invalid source for event: %s" % event.source, 1)
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

        nextid = self.query("SELECT nextval('eventq_eventqid_seq')")[0][0]
        statement = """INSERT INTO eventq
                       (eventqid, subid, netboxid, deviceid, eventtypeid,
                        state, value, source, target)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        values = (nextid, event.serviceid, event.netboxid, event.deviceid,
                  event.eventtype, state, value, event.source, "eventEngine")
        self.execute(statement, values)

        statement = """INSERT INTO eventqvar
                       (eventqid, var, val) VALUES
                       (%s, %s, %s)"""
        values = (nextid, 'descr', event.info)
        self.execute(statement, values)

    def hostsToPing(self):
        query = """SELECT netboxid, deviceid, sysname, ip, up FROM netbox """
        try:
            self._hostsToPing = self.query(query)
        except dbError:
            return self._hostsToPing
        return self._hostsToPing

    def getCheckers(self, useDbStatus, onlyactive = 1):
        query = """SELECT serviceid, property, value
        FROM serviceproperty
        order BY serviceid"""

        property = {}
        try:
            properties = self.query(query)
        except dbError:
            return self._checkers
        for serviceid, prop, value in properties:
            if serviceid not in property:
                property[serviceid] = {}
            if value:
                property[serviceid][prop] = value

        query = """SELECT serviceid ,service.netboxid, netbox.deviceid,
        service.active, handler, version, ip, sysname, service.up
        FROM service JOIN netbox ON
        (service.netboxid=netbox.netboxid) order by serviceid"""
        try:
            fromdb = self.query(query)
        except dbError:
            return self._checkers

        self._checkers = []
        for each in fromdb:
            if len(each) == 9:
                (serviceid, netboxid, deviceid, active, handler, version, ip,
                 sysname, up) = each
            else:
                debug("Invalid checker: %s" % each, 2)
                continue
            checker = checkermap.get(handler)
            if not checker:
                debug("no such checker: %s" % handler, 2)
                continue
            service = {
                'id':serviceid,
                'netboxid':netboxid,
                'ip':ip,
                'deviceid':deviceid,
                'sysname':sysname,
                'args':property.get(serviceid,{}),
                'version':version
                }

            kwargs = {}
            if useDbStatus:
                if up == 'y':
                    up = Event.UP
                else:
                    up = Event.DOWN
                kwargs['status'] = up

            try:
                newChecker = checker(service, **kwargs)
            except Exception, why:
                debug("Checker %s (%s) failed to init. This checker will "
                      "remain DISABLED:\n%s" % (handler, checker,
                                                traceback.format_exc()), 2)
                continue

            if onlyactive and not active:
                continue
            else:
                setattr(newChecker, 'active', active)

            self._checkers += [newChecker]
        debug("Returned %s checkers" % len(self._checkers))
        return self._checkers


    def verify_rrd(self, filename):
        """Verifies that a given RRD file is registered in the db.

        Returns: The netboxid of the netbox to which this RRD file belongs.

        If the RRD file is unknown, a UnknownRRDFileError is raised.

        """
        statement = """SELECT rrd_fileid, netboxid FROM rrd_file
                       WHERE path=%s AND filename=%s"""
        rows = self.query(statement, (os.path.dirname(filename),
                                      os.path.basename(filename)))
        if len(rows) > 0:
            (rrd_fileid, netboxid) = rows[0]
            return netboxid
        raise UnknownRRDFileError(filename)

    def get_existing_rrd(self, netboxid, serviceid=None):
        """Returns the filename tuple of the last registered RRD file
        for the given netboxid/serviceid combination"""
        if serviceid:
            where = """WHERE netboxid=%s AND subsystem='serviceping' AND
                       key='serviceid' AND value=%s"""
            values = (netboxid, str(serviceid))
        else:
            where = "WHERE netboxid=%s AND subsystem='pping'"
            values = (netboxid,)

        statement = """SELECT path, filename FROM rrd_file %s
                       ORDER BY rrd_fileid DESC LIMIT 1""" % where
        rows = self.query(statement, values)
        if len(rows) > 0:
            return os.path.join(*rows[0])
        else:
            raise UnknownRRDFileError(netboxid, serviceid)

    def rename_rrd(self, from_file, to_file):
        """Renames a referenced RRD file in the database, but not on disk"""
        statement = """UPDATE rrd_file
                       SET path=%s, filename=%s
                       WHERE path=%s AND filename=%s"""
        self.execute(statement,
                     (os.path.dirname(to_file), os.path.basename(to_file),
                      os.path.dirname(from_file), os.path.basename(from_file)))

    def reconnect_rrd(self, filename, netboxid):
        """Reconnects a known, disconnected RRD file with a netboxid."""
        statement = """UPDATE rrd_file
                       SET netboxid=%s
                       WHERE path=%s AND
                             filename=%s AND
                             netboxid IS NULL"""
        return self.execute(statement, (netboxid,
                                        os.path.dirname(filename),
                                        os.path.basename(filename)))

    def registerRrd(self, filename, step, netboxid, subsystem, key="",
                    val=""):
        rrdid = self.query("SELECT nextval('rrd_file_rrd_fileid_seq')")[0][0]
        if key and val:
            statement = """INSERT INTO rrd_file
                           (rrd_fileid, path, filename, step, netboxid,
                            key, value, subsystem)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (rrdid,
                      os.path.dirname(filename), os.path.basename(filename),
                      step, netboxid, key, val, subsystem)
        else:
            statement = """INSERT INTO rrd_file
                           (rrd_fileid, path, filename, step, netboxid,
                            subsystem)
                           VALUES (%s, %s, %s, %s, %s, %s)"""
            values = (rrdid,
                      os.path.dirname(filename), os.path.basename(filename),
                      step, netboxid, subsystem)
        self.execute(statement, values)
        return rrdid

    def registerDS(self, rrd_fileid, name, descr, dstype, unit):
        statement = """INSERT INTO rrd_datasource
        (rrd_fileid, name, descr, dstype, units) VALUES
        (%s, %s, %s, %s, %s)"""
        self.execute(statement, (rrd_fileid, name, descr, dstype, unit))
