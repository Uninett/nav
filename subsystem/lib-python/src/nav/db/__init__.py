"""
$Id: x1$

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
    if not hasattr(nav, 'CachedObject'):
        reload(nav)
        import sys
        sys.stderr.write('MORTEN-DEBUG: CachedObject not found, module nav reloaded;' +
                         'Extremely strange mod_python bug forces this ugly hack\n')
                  
    from nav import CachedObject
    global _connectionCache
    cacheKey = '%s_%s' % (scriptName, database)

    # If the connection object already exists in the connection cache,
    # we return this instead.  Here we should also perform some checks
    # as to whether the connection is still valid.
    if _connectionCache.has_key(cacheKey):
        return _connectionCache[cacheKey].object
    else:
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
