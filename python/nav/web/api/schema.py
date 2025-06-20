#
# Copyright (C) 2025 Sikt
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
import re

PUBLIC_SCHEMA_FILTER = re.compile(r'^/api/\d+/.*$')


def public_schema_filter(endpoints):
    """drf-spectacular preprocessing filter to filter out DRF endpoints we don't want to 'expose' as public API.

    This is mostly because of NAV's weird DRF usage, where the latest API version is bound both to the /api/ and
    /api/<version>/ URL prefixes.  Some NAV apps also provide internal APIs that should not be exposed as part of the
    public schema.  This function basically ensures only endpoints with the /api/<version>/ prefix are included in
    the schema.
    """
    for endpoint in endpoints:
        path, _path_regex, _method, _callback = endpoint
        if PUBLIC_SCHEMA_FILTER.match(path):
            yield endpoint
