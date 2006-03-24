# -*- coding: ISO8859-1 -*-
# $Id$
#
# Copyright 2003 Norwegian University of Science and Technology
# Copyright 2006 UNINETT AS
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
# Authors: Morten Vold <morten.vold@itea.ntnu.no>
#
"""
Provides common database functionality for NAV.
"""
import atexit
import time
import psycopg
import nav
from nav import config

db = None
driver = psycopg
_connectionCache = nav.ObjectCache()

class ConnectionObject(nav.CacheableObject):
    """
    Specialization of nav.CacheableObject to implement psycopg
    connection caching.
    """
    # Minimum number of seconds to wait between validating
    # connections.
    validation_interval = 60
    
    def __init__(self, object, key):
        super(ConnectionObject, self).__init__(object)
        self.key = key
        self.lastValidated = time.time()

    def isInvalid(self):
        """Attempt to check whether the database connection has become
        invalid, which would typically be caused by the connection
        having been terminated without our knowledge or consent.
        """
        # This method will be called almost every time a getConnection
        # call is executed, resulting in a ping or SELECT 1 being
        # executed quite often.  If no transaction is open in this
        # connection, executing SELECT 1 will start a new transaction.
        # Since the isolation level is READ COMMITTED, any further use
        # of this connection will see the database as it was at the
        # time the transaction was started, which could potentially be
        # bad for your health.
        #
        # To mitigate this somewhat, we make sure to never ping the
        # connection more often than once every 60 seconds.  This
        # means less connection overhead, and less running into idle
        # transactions (hopefully).
        #
        # Of course, this is all an ugly hack, but we do it becase
        # psycopg will not let us check the connection status or tell
        # us whether we are currently inside an open transaction.
        if time.time() < self.lastValidated + self.validation_interval:
            # Not invalid
            return False
        
        try:
            if self.ping():
                self.lastValidated = time.time()
                return False
        except (psycopg.ProgrammingError, psycopg.OperationalError):
            import sys
            sys.stderr.write('DB-DEBUG: Invalid connection object (%s), age=%s\n' % (repr(self.key), self.age()))
            self.object.close()
            return True
        except psycopg.InterfaceError:
            import sys
            sys.stderr.write('DB-DEBUG: Connection may already be closed (%s)\n' % repr(self.key))
            return True

    def ping(self):
        """'ping' the database connection.

        Executes a simple query, like SELECT 1.  If no exceptions are
        raised, the database connection should still be up.
        """
        cursor = self.object.cursor()
        cursor.execute('SELECT 1')
        # If we got this far withouth exceptions, we did OK
        return 1

def escape(string):
    return str(psycopg.QuotedString(string))

def getConnection(scriptName, database='manage'):
    """
    Returns an open database connection, as configured in db.conf for
    the given scriptName.  Connections are cached, so that future
    calls using the same parameters will receive an already open
    connection.
    """
    import nav
    global _connectionCache

    # Get the config setup for the requested connection
    conf = config.readConfig('db.conf')
    dbname = conf['db_%s' % database]
    user   = conf['script_%s' % scriptName]
    pw     = conf['userpw_%s' % user]
    cacheKey = (dbname, user)

    # First, invalidate any dead connections.  Return a connection
    # object from the cache if one exists, open a new one if not.
    _connectionCache.invalidate()
    try:
        connection = _connectionCache[cacheKey].object
    except KeyError:
        connection = psycopg.connect('host=%s dbname=%s user=%s password=%s' %
                                     (conf['dbhost'], dbname, user, pw))
        connection.autocommit(0)
        connection.set_isolation_level(1)
        connObject = ConnectionObject(connection, cacheKey)
        _connectionCache.cache(connObject)
        
    return connection

def setDefaultConnection(conn):
    global db, cursor
    db = conn
    cursor = db.cursor

def closeConnections():
    """Close all cached database connections"""
    for connection in _connectionCache.values():
        try:
            connection.object.close()
        except psycopg.InterfaceError:
            pass

###### Initialization ######

if not db:
    setDefaultConnection(getConnection('default'));

# Psycopg doesn't seem to close connections when they are garbage
# collected. Here we try to clean up our act on system exit, to
# avoid the numerous "unexpected EOF on client connection" that NAV
# seems to generate in the PostgreSQL logs.
atexit.register(closeConnections)
