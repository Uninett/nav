# -*- coding: ISO8859-1 -*-
#
# Copyright 2002 Norwegian University of Science and Technology
#
# This file is part of Network Administration Visualized (NAV)
#
# NAV is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# NAV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NAV; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# $Id: $
# Authors: Magnus Nordseth <magnun@itea.ntnu.no>
#          Erik Gorset     <erikgors@stud.ntnu.no>
#
"""
This class is an abstraction of the database operations needed
by the service monitor.

It implements the singleton pattern, ensuring only one instance
is used at a time.
"""

import threading
import checkermap
import psycopg
import Queue
import time
import atexit
import traceback

from event import Event
from service import Service
from debug import debug


def db(conf):
    if _db._instance is None:
        _db._instance=_db(conf)

    return _db._instance

class dbError(Exception):
    pass

class UnknownRRDFileError(Exception):
    pass

class _db(threading.Thread):
    _instance=None
    def __init__(self, conf):
        threading.Thread.__init__(self)
        self.conf = conf
        self.setDaemon(1)
        self.queue = Queue.Queue()
        self._hostsToPing = []
        self._checkers = []

    def connect(self):
        try:
            host = self.conf['dbhost']
            user = self.conf['script_servicemon']
            passwd = self.conf['userpw_%s'%user]
            dbname = self.conf['db_nav']
            self.db = \
                    psycopg.connect("host = %s user = %s dbname = %s password = %s"
                                    % (host, user, dbname, passwd))
            atexit.register(self.db.close)

            debug("Successfully (re)connected to NAVdb")
            self.db.autocommit(0)
        except Exception, e:
            debug("Couldn't connect to db.", 2)
            debug(str(e),2)
            self.db=None

    def cursor(self):
        try:
            cursor = self.db.cursor()
            # this is a very dirty workaround...
            cursor.execute('SELECT 1')
        except:
            debug("Could not get cursor. Trying to reconnect...", 2)
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
                debug("Failed to commit event, rescheduling...",7)
                self.newEvent(event)
                time.sleep(5)

    def query(self, statement, commit=1):
        try:
            cursor=self.cursor()
            debug("Executing: %s" % statement,7)
            cursor.execute(statement)
            if commit:
                self.db.commit()
            return cursor.fetchall()
        except Exception, e:
            debug("Failed to execute query: %s" % statement, 2)
            debug(str(e))
            if commit:
                try:
                    self.db.rollback()
                except:
                    debug("Failed to rollback",2)
            raise dbError()
    def execute(self, statement, commit=1):
        try:
            cursor=self.cursor()
            debug("Executing: %s" % statement,5)
            cursor.execute(statement)
            if commit:
                try:
                    self.db.commit()
                except:
                    debug("Failed to commit", 2)
        except psycopg.IntegrityError, e:
            debug(str(e), 2)
            debug("Throwing away update...", 2)
        except Exception, e:
            debug("Could not execute statement: %s" % statement, 2)
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
            statement = """UPDATE service SET
            version = '%s' WHERE serviceid = %i""" % (event.version,
                                                      event.serviceid
                                                      )
            self.execute(statement)
            return
        
        if event.status == Event.UP:
            value = 100
            state = 'e'
        elif event.status == Event.DOWN:
            value = 1
            state = 's'

        nextid = self.query("SELECT nextval('eventq_eventqid_seq')")[0][0]
        statement = """INSERT INTO eventq
(eventqid, subid, netboxid, deviceid, eventtypeid, state, value, source, target)
VALUES (%i, %i, %i,%i, '%s','%s', %i, '%s','%s' )""" % (nextid,
                                                        event.serviceid,
                                                        event.netboxid,
                                                        event.deviceid,
                                                        event.eventtype,
                                                        state,
                                                        value,
                                                        event.source,
                                                        "eventEngine"
                                                        )
        self.execute(statement)
        statement = """INSERT INTO eventqvar
        (eventqid, var, val) VALUES
        (%i, '%s', '%s')""" % (nextid, 'descr', event.info.replace("'","\\'"))
        # self.execute(statement)
        debug("Executed: %s" % statement)

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
        for serviceid,prop,value in properties:
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
                serviceid,netboxid,deviceid,active,handler,version,ip,sysname,up = each
            else:
                debug("Invalid checker: %s" % each,2)
                continue
            checker = checkermap.get(handler)
            if not checker:
                debug("no such checker: %s" % handler,2)
                continue
            service={'id':serviceid,
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
                    up=Event.UP
                else:
                    up=Event.DOWN
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
                setattr(newChecker,'active',active)

            self._checkers += [newChecker]
        debug("Returned %s checkers" % len(self._checkers))
        return self._checkers


    def verify_rrd(self, path, filename):
        """Verifies that a given RRD file is registered in the db.

        Returns: The netboxid of the netbox to which this RRD file belongs.

        If the RRD file is unknown, a UnknownRRDFileError is raised.

        BUGS: Big gaping hole: Does not use parameterized SQL statement.
        """
        statement = \
            """SELECT rrd_fileid, netboxid FROM rrd_file
               WHERE path='%s' AND
                     filename='%s'""" % (path, filename)
        rows = self.query(statement)
        if len(rows) > 0:
            (rrd_fileid, netboxid) = rows[0]
            return netboxid
        raise UnknownRRDFileError(path, filename)

    def reconnect_rrd(self, path, filename, netboxid):
        """Reconnects a known, disconnected RRD file with a netboxid."""
        statement = \
            """UPDATE rrd_file
               SET netboxid=%d
               WHERE path='%s' AND
                     filename='%s' AND
                     netboxid IS NULL""" % (netboxid, path, filename)
        return self.execute(statement)

    def registerRrd(self, path, filename, step, netboxid, subsystem, key="",val=""):
        rrdid = self.query("SELECT nextval('rrd_file_rrd_fileid_seq')")[0][0]
        if key and val:
            statement = """INSERT INTO rrd_file
            (rrd_fileid, path, filename, step, netboxid, key, value, subsystem) values
            (%s, '%s','%s',%s,%s,'%s',%s,'%s')""" %    (rrdid, path, filename,
                                 step, netboxid, key, val, subsystem)
        else:
            statement = """INSERT INTO rrd_file
            (rrd_fileid, path, filename, step, netboxid, subsystem) VALUES
            (%s,'%s','%s',%s,%s,'%s')""" %(rrdid, path, filename,
                               step, netboxid, subsystem)
        self.execute(statement)
        return rrdid
    def registerDS(self, rrd_fileid, name, descr, dstype, unit):
        statement = """INSERT INTO rrd_datasource
        (rrd_fileid, name, descr, dstype, units) VALUES
        (%s, '%s', '%s', '%s', '%s')""" % (rrd_fileid, name, descr, dstype, unit)
        self.execute(statement)
