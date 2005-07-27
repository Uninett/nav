# -*- coding: ISO8859-1 -*-
# $Id$
#
# Copyright 2003 Norwegian University of Science and Technology
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
    def __init__(self, object, key):
        super(ConnectionObject, self).__init__(object)
        self.key = key

    def isInvalid(self):
        try:
            cursor = self.object.cursor()
            cursor.execute('SELECT 1')
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
