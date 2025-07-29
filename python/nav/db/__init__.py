#
# Copyright (C) 2006-2009 Uninett AS
# Copyright (C) 2022 Sikt
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""
Provides common database functionality for NAV.
"""

import atexit
from functools import wraps
import logging
import os
import sys
import time

import psycopg2
import psycopg2.extensions

import nav
from nav import config

_logger = logging.getLogger('nav.db')
_connection_cache = nav.ObjectCache()
driver = psycopg2


class ConnectionObject(nav.CacheableObject):
    """
    Specialization of nav.CacheableObject to implement psycopg
    connection caching.
    """

    def __init__(self, object_, key):
        super(ConnectionObject, self).__init__(object_)
        self.key = key
        self.last_validated = time.time()

    def is_invalid(self):
        """Attempt to check whether the database connection has become
        invalid, which would typically be caused by the connection
        having been terminated without our knowledge or consent.
        """
        try:
            try:
                if self.ping():
                    self.last_validated = time.time()
                    return False
            except (psycopg2.ProgrammingError, psycopg2.OperationalError):
                _logger.debug(
                    'Invalid connection object (%r), age=%s', self.key, self.age()
                )
                self.object.close()
                return True
        except psycopg2.InterfaceError:
            _logger.debug('Connection may already be closed (%r)', self.key)
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
    """Escape a string for use in SQL statements.

    ..warning:: You should be using parameterized queries if you can!

    """
    quoted = psycopg2.extensions.QuotedString(string)
    result = quoted.getquoted()
    return result if isinstance(result, str) else result.decode("utf-8")


def get_connection_parameters(script_name='default', database='nav'):
    """Return a tuple of database connection parameters.

    The parameters are read from db.conf, using script_name as a
    lookup key to find the database user to log in as.

    :returns: A tuple containing the following elements:
              (dbhost, dbport, dbname, user, password)

    """
    # Get the config setup for the requested connection
    conf = config.read_flat_config('db.conf')
    dbhost = conf['dbhost']
    dbport = conf['dbport']

    db_option = 'db_%s' % database
    if db_option not in conf:
        _logger.debug(
            "connection parameter for database %s doesn't exist, "
            "reverting to default 'db_nav'",
            database,
        )
        db_option = 'db_nav'
    dbname = conf[db_option]

    user_option = 'script_%s' % script_name
    if user_option not in conf:
        _logger.debug(
            "connection parameter for script %s doesn't exist, reverting to default",
            script_name,
        )
        user_option = 'script_default'
    user = conf[user_option]

    password = conf['userpw_%s' % user]
    return dbhost, dbport, dbname, user, password


def get_connection_string(db_params=None, script_name='default'):
    """Returns a psycopg connection string.

    :param db_params: A tuple of db connection parameters.  If omitted,
                      get_connection_parameters is called to get this data,
                      with script_name as its argument.

    :param script_name: Script name to use for looking up connection
                        info, if dbparams is supplied.

    :returns: A suitable dsn string to use when calling psycopg2.connect()

    """
    if not db_params:
        db_params = get_connection_parameters(script_name)
    dbhost, dbport, dbname, dbuser, dbpasswd = db_params
    appname = os.path.basename(sys.argv[0]) or script_name
    conn_string = (
        "host={dbhost} port={dbport} dbname={dbname} user={dbuser}"
        " password={dbpasswd}"
        " application_name='{appname} (NAV legacy)'"
    )
    return conn_string.format(**locals())


def getConnection(scriptName, database='nav'):
    """
    Returns an open database connection, as configured in db.conf for
    the given scriptName.  Connections are cached, so that future
    calls using the same parameters will receive an already open
    connection.
    """
    (dbhost, port, dbname, user, password) = get_connection_parameters(
        scriptName, database
    )
    cache_key = (dbname, user)

    # First, invalidate any dead connections.  Return a connection
    # object from the cache if one exists, open a new one if not.
    _connection_cache.invalidate()
    try:
        connection = _connection_cache[cache_key].object
    except KeyError:
        connection = psycopg2.connect(
            get_connection_string((dbhost, port, dbname, user, password))
        )
        _logger.debug(
            "Opened a new database connection, scriptName=%s, dbname=%s, user=%s",
            scriptName,
            dbname,
            user,
        )
        # Se transaction isolation level READ COMMITTED
        connection.set_isolation_level(1)
        connection.set_client_encoding('utf8')
        conn_object = ConnectionObject(connection, cache_key)
        _connection_cache.cache(conn_object)

    return connection


def closeConnections():
    """Close all cached database connections"""
    for connection in _connection_cache.values():
        try:
            connection.object.close()
        except psycopg2.InterfaceError:
            pass


def commit_all_connections():
    """Attempts to commit the current transactions on all cached connections"""
    conns = (v.object for v in _connection_cache.values())
    for conn in conns:
        conn.commit()


def retry_on_db_loss(count=3, delay=2, fallback=None, also_handled=None):
    """Decorates functions to retry them a set number of times in the face of
    exceptions that appear to be database connection related. If the function
    still fails with database errors after the set number of retries,
    a fallback function is called, or the caught exception is re-raised.

    :param count: Maximum number of times to retry the function
    :param delay: The number of seconds to sleep between each retry
    :param fallback: A function to run when all retry attempts fail. If
                     set to None, the caught exception will be re-raised.
    :param also_handled: A list of exception classes to catch in addition to
                         the relevant ones from the psycopg2 library.

    """
    if fallback:
        assert callable(fallback)
    handled = (psycopg2.OperationalError, psycopg2.InterfaceError)
    if also_handled:
        handled = handled + tuple(also_handled)

    def _retry_decorator(func):
        def _retrier(*args, **kwargs):
            remaining = count
            while remaining:
                try:
                    return func(*args, **kwargs)
                except handled:
                    remaining -= 1
                    _logger.error(
                        "cannot establish db connection. retries remaining: %d",
                        remaining,
                    )
                    if remaining:
                        time.sleep(delay)
                        continue
                    elif fallback:
                        fallback()
                    else:
                        raise

        return wraps(func)(_retrier)

    return _retry_decorator


###### Initialization ######


# Psycopg doesn't seem to close connections when they are garbage
# collected. Here we try to clean up our act on system exit, to
# avoid the numerous "unexpected EOF on client connection" that NAV
# seems to generate in the PostgreSQL logs.
atexit.register(closeConnections)


class ConnectionParameters(object):
    """Database Connection parameters"""

    def __init__(self, dbhost, dbport, dbname, user, password):
        self.dbhost = dbhost
        self.dbport = dbport
        self.dbname = dbname
        self.user = user
        self.password = password

    @classmethod
    def from_config(cls):
        """Initializes and returns parameters from NAV's config"""
        return cls(*get_connection_parameters())

    @classmethod
    def from_environment(cls):
        """Initializes and returns parameters from environment vars"""
        params = [
            os.environ.get(v, None)
            for v in ('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD')
        ]
        return cls(*params)

    @classmethod
    def for_postgres_user(cls):
        """Returns parameters suitable for logging in the postgres user using
        PostgreSQL command line clients.
        """
        config = cls.from_config()
        environ = cls.from_environment()

        if not environ.dbhost and config.dbhost != 'localhost':
            environ.dbhost = config.dbhost
        if not environ.dbport and config.dbport:
            environ.dbport = config.dbport

        return environ

    def export(self, environ):
        """Exports parameters to environ.

        Supply os.environ to export to subprocesses.

        """
        added_environ = dict(
            zip(
                ('PGHOST', 'PGPORT', 'PGDATABASE', 'PGUSER', 'PGPASSWORD'),
                self.as_tuple(),
            )
        )
        for var, val in added_environ.items():
            if val:
                environ[var] = val

    def as_tuple(self):
        """Returns parameters as a tuple"""
        return (self.dbhost, self.dbport, self.dbname, self.user, self.password)

    def __str__(self):
        return get_connection_string(self.as_tuple())
