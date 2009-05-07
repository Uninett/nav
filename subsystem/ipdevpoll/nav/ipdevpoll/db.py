# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Database related functionality for ipdevpoll."""

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
