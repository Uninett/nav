"""Database related functionality for ipdevpoll."""

__author__ = "Morten Brekkevold (morten.brekkevold@uninett.no)"
__copyright__ = "Copyright 2008 UNINETT AS"
__license__ = "GPLv2"

from twisted.enterprise import adbapi

from nav.db import get_connection_string

_dbpool = None

def get_db_pool():
    """Possibly create and return a database connection pool.

    This function creates and returns a
    twisted.enterprise.adbapi.ConnectionPool based on NAV's db.conf.
    Only a single pool will be created, multiple calls to this
    function will return the same pool object.

    """
    global _dbpool
    if _dbpool is None:
        conn_str = get_connection_string()
        _dbpool = adbapi.ConnectionPool('psycopg', conn_str)
    return _dbpool
