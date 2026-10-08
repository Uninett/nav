#
# Copyright (C) 2026 Sikt
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
"""OpenAPI schema generation helpers for the NAV REST API."""

import re

PUBLIC_SCHEMA_FILTER = re.compile(r'^/api/\d+/.*$')


def public_schema_filter(endpoints):
    """Filter out DRF endpoints we don't want to expose as a public API.

    NAV binds the latest API version both to the ``/api/`` and ``/api/<version>/``
    URL prefixes, and some NAV apps provide internal APIs that should not be part
    of the public schema. This drf-spectacular preprocessing hook keeps only
    endpoints with an ``/api/<version>/`` prefix, which both de-duplicates the
    double-mounted endpoints and excludes internal app APIs.
    """
    for endpoint in endpoints:
        path, _path_regex, _method, _callback = endpoint
        if PUBLIC_SCHEMA_FILTER.match(path):
            yield endpoint
