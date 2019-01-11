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

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:  # Django <= 1.9
    MiddlewareMixin = object

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
            conn.rollback()

        return response
