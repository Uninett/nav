"""
$Id$

This file is part of the NAV project.

Provides common database functionality for NAV.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
import psycopg
from nav import config, ObjectCache, CacheableObject

db = None
driver = psycopg
_connectionCache = ObjectCache()

class ConnectionObject(CacheableObject):
    """
    Specialization of nav.CacheableObject to implement psycopg
    connection caching.
    """
    def __init__(self, object, key):
        CacheableObject.__init__(self, object)
        self.key = key

    def isInvalid(self):
        try:
            cursor = self.object.cursor()
            cursor.execute('SELECT 1')
            return False
        except psycopg.ProgrammingError:
            import sys
            sys.stderr.write('DB-DEBUG: Invalid connection object (%s), age=%s\n' % (repr(self.key), self.age()))
            self.object.close()
            return True
        except psycopg.InterfaceError:
            import sys
            sys.stderr.write('DB-DEBUG: Connection may already be closed (%s)\n' % repr(self.key))
            return True

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
    from nav import CachedObject
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
        connection.autocommit(1)
        connObject = ConnectionObject(connection, cacheKey)
        _connectionCache.cache(connObject)
        
    return connection

def setDefaultConnection(conn):
    global db, cursor
    db = conn
    cursor = db.cursor
    db.autocommit(1)

###### Initialization ######

if not db:
    setDefaultConnection(getConnection('default'));
