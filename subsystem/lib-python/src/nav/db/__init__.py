"""
$Id$

This file is part of the NAV project.

Provides common database functionality for NAV.

Copyright (c) 2003 by NTNU, ITEA nettgruppen
Authors: Morten Vold <morten.vold@itea.ntnu.no>
"""
import psycopg
from nav import config

db = None
driver = psycopg
_connectionCache = {}

def escape(string):
    return str(psycopg.QuotedString(string))

def getConnection(scriptName, database='nav'):
    """
    Returns an open database connection, as configured in db.conf for
    the given scriptName.  Connections are cached, so that future
    calls using the same parameters will receive an already open
    connection.
    """
    import nav
    from nav import CachedObject
    global _connectionCache
    cacheKey = '%s_%s' % (scriptName, database)

    # If the connection object already exists in the connection cache,
    # we check whether it is still open/valid.  If it is, we return
    # this instead of a new connection.
    if _connectionCache.has_key(cacheKey):
        connection = _connectionCache[cacheKey].object
        try:
            cursor = connection.cursor()
            cursor.execute('SELECT 1')
            return connection
        except psycopg.ProgrammingError:
            import sys
            sys.stderr.write('DB-DEBUG: Reaping a dead connection object\n')
            connection.close()
            del cursor
            del connection
            del _connectionCache[cacheKey]

    # If we got this far, we did not return an existing connection.
    conf = config.readConfig('db.conf')
    dbname = conf['db_%s' % database]
    user   = conf['script_%s' % scriptName]
    pw     = conf['userpw_%s' % user]
        
    connection = psycopg.connect('host=%s dbname=%s user=%s password=%s' %
                                 (conf['dbhost'], dbname, user, pw))

    _connectionCache[cacheKey] = CachedObject(connection)
    return connection

def setDefaultConnection(conn):
    global db, cursor
    db = conn
    cursor = db.cursor
    db.autocommit(1)

###### Initialization ######

if not db:
    setDefaultConnection(getConnection('default'));
