#
# Copyright (C) 2013 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Various functionality to bridge legacy NAV code with Django"""

import psycopg2

from django.utils.deprecation import MiddlewareMixin

from nav import db


class LegacyCleanupMiddleware(MiddlewareMixin):
    """Django middleware to clean up NAV legacy database connections at the
    end of each request cycle.

    """

    def process_response(self, _request, response):
        """Rolls back any uncommitted legacy database connections,
        to avoid idling indefinitely in transactions.

        """
        connections = (v.object for v in db._connection_cache.values())
        for conn in connections:
            try:
                conn.rollback()
            except psycopg2.Error:
                # The cached connection may have died out-of-band during the
                # request (database reboot, server-side termination, network
                # drop) after getConnection() last validated it. psycopg2 does
                # not flag such a connection as closed until the failing I/O, so
                # the rollback here is what raises. Swallow it so cleanup does
                # not turn into an HTTP 500; getConnection() validates and
                # replaces the dead connection on the next request.
                pass

        return response
