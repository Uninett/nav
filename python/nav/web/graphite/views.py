#
# Copyright (C) 2013 UNINETT
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
# details.  You should have received a copy of the GNU General Public License
# along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
import urllib2
from django.http import HttpResponse
from nav.metrics import CONFIG

import logging
LOGGER = logging.getLogger(__name__)


def index(request, uri):
    """
    Proxies render requests to graphite-web, as configured in graphite.conf
    """
    base = CONFIG.get('graphiteweb', 'base')
    query = _inject_default_format(request.GET)
    url = base + uri + ('?' + query) if query else ''

    LOGGER.debug("proxying request to %r", url)
    req = urllib2.Request(url)
    response = urllib2.urlopen(req)
    headers = response.info()
    content_type = headers.getheader('Content-Type', 'text/html')
    return HttpResponse(response.read(), content_type=content_type)


def _inject_default_format(query):
    """
    Injects a default format argument to a render request, unless it was
    explicitly supplied by the client.
    """
    format_ = CONFIG.get('graphiteweb', 'format')
    query = query.copy()
    if not 'format' in query:
        query['format'] = format_

    return query.urlencode()
