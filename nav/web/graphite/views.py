#
# Copyright (C) 2013 Uninett AS
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
from django.utils.six.moves.urllib.request import Request, urlopen
from django.utils.six.moves.urllib.error import HTTPError
from django.utils.six.moves.urllib.parse import urljoin
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotAllowed
from nav.metrics import CONFIG

import logging
LOGGER = logging.getLogger(__name__)


def index(request, uri):
    """
    Proxies render requests to graphite-web, as configured in graphite.conf
    """
    base = CONFIG.get('graphiteweb', 'base')

    if request.method in ('GET', 'HEAD'):
        query = _inject_default_arguments(request.GET)
        url = urljoin(base, uri + ('?' + query) if query else '')
        req = Request(url)
        data = None
    elif request.method == 'POST':
        data = _inject_default_arguments(request.POST)
        url = urljoin(base, uri)
        req = Request(url, data)
    else:
        return HttpResponseNotAllowed(['GET', 'POST', 'HEAD'])

    LOGGER.debug("proxying request to %r", url)
    try:
        proxy = urlopen(req)
    except HTTPError as error:
        status = error.code
        headers = error.hdrs
        output = error.fp.read()

        LOGGER.error("%s error on graphite render request: "
                     "%r with arguments: %r", status, url, data)

    else:
        status = proxy.getcode()
        headers = proxy.info()
        output = proxy.read()

    content_type = headers.getheader('Content-Type', 'text/html')

    if request.method == 'HEAD':
        response = HttpResponse(content_type=content_type, status=status)
        response['Content-Length'] = headers.getheader('Content-Length', '0')
    else:
        response = HttpResponse(output, content_type=content_type, status=status)

    response['X-Where-Am-I'] = request.get_full_path()
    return response


def _inject_default_arguments(query):
    """
    Injects default arguments to a render request, unless they are already
    explicitly supplied by the client.
    """
    format_ = CONFIG.get('graphiteweb', 'format')
    query = query.copy()

    if not 'format' in query:
        query['format'] = format_
    if not 'tz' in query and settings.TIME_ZONE:
        query['tz'] = settings.TIME_ZONE

    return query.urlencode()
