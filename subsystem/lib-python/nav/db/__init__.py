# -*- coding: utf-8 -*-
#
# Copyright (C) 2003 Norwegian University of Science and Technology
# Copyright (C) 2006-2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details. 
# You should have received a copy of the GNU General Public License along with
# NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Provides common database functionality for NAV.
"""
import atexit
import time
import psycopg
import nav
from nav import config
import logging

logger = logging.getLogger('nav.db')
driver = psycopg
_connectionCache = nav.ObjectCache()

class ConnectionObject(nav.CacheableObject):
    """
    Specialization of nav.CacheableObject to implement psycopg
    connection caching.
    """
    def __init__(self, object, key):
        super(ConnectionObject, self).__init__(object)
        self.key = key
        self.lastValidated = time.time()

    def isInvalid(self):
        """Attempt to check whether the database connection has become
        invalid, which would typically be caused by the connection
        having been terminated without our knowledge or consent.
        """
        try:
            if self.ping():
                self.lastValidated = time.time()
                return False
        except (psycopg.ProgrammingError, psycopg.OperationalError):
            logger.debug('Invalid connection object (%s), age=%s' % (repr(self.key), self.age()))
            self.object.close()
            return True
        except psycopg.InterfaceError:
            logger.debug('Connection may already be closed (%s)' % repr(self.key))
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

def get_connection_parameters(script_name='default', database='nav'):
    """Return a tuple of database connection parameters.

    The parameters are read from db.conf, using script_name as a
    lookup key to find the database user to log in as.

    Returns a tuple containing the following elements:
  
    (dbhost, dbport, dbname, user, password)
    """
    # Get the config setup for the requested connection
    conf = config.readConfig('db.conf')
    dbhost = conf['dbhost']
    dbport   = conf['dbport']

    db_option = 'db_%s' % database
    if db_option not in conf:
        logger.debug("connection parameter for database %s doesn't exist, "
                     "reverting to default 'db_nav'", database)
        db_option = 'db_nav'
    dbname = conf[db_option]

    user_option = 'script_%s' % script_name
    if user_option not in conf:
        logger.debug("connection parameter for script %s doesn't exist, "
                     "reverting to default", script_name)
        user_option = 'script_default'
    user   = conf[user_option]

    pw     = conf['userpw_%s' % user]
    return (dbhost, dbport, dbname, user, pw)

def get_connection_string(db_params=None, script_name='default'):
    """Return a psycopg connection string.

      db_params -- A tuple of db connection parameters.  If omitted,
                   get_connection_parameters is called to get this
                   data, with script_name as its argument.

      script_name -- Script name to use for looking up connection
                     info, if dbparams is supplied.

    """
    if not db_params:
        db_params = get_connection_parameters(script_name)
    conn_string = "host=%s port=%s dbname=%s user=%s password=%s" % db_params
    return conn_string

def getConnection(scriptName, database='nav'):
    """
    Returns an open database connection, as configured in db.conf for
    the given scriptName.  Connections are cached, so that future
    calls using the same parameters will receive an already open
    connection.
    """
    import nav
    global _connectionCache

    (dbhost, port, dbname, user, pw) = \
             get_connection_parameters(scriptName, database)
    cacheKey = (dbname, user)

    # First, invalidate any dead connections.  Return a connection
    # object from the cache if one exists, open a new one if not.
    _connectionCache.invalidate()
    try:
        connection = _connectionCache[cacheKey].object
    except KeyError:
        connection = psycopg.connect(get_connection_string(
                (dbhost, port, dbname, user, pw)))
        logger.debug("Opened a new database connection, scriptName=%s, "
                     "dbname=%s, user=%s", scriptName, dbname, user)
        connection.autocommit(0)
        connection.set_isolation_level(1)
        connObject = ConnectionObject(connection, cacheKey)
        _connectionCache.cache(connObject)
        
    return connection

def closeConnections():
    """Close all cached database connections"""
    for connection in _connectionCache.values():
        try:
            connection.object.close()
        except psycopg.InterfaceError:
            pass

###### Initialization ######

# Psycopg doesn't seem to close connections when they are garbage
# collected. Here we try to clean up our act on system exit, to
# avoid the numerous "unexpected EOF on client connection" that NAV
# seems to generate in the PostgreSQL logs.
atexit.register(closeConnections)
