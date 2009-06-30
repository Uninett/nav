#
# Copyright (C) 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 2 as published by the Free
# Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#

from django.template import RequestContext
from django.http import HttpResponse

from nav.django.shortcuts import render_to_response
from nav.web.templates.GeomapTemplate import GeomapTemplate
from nav.web.geomap.utils import get_formatted_data, format_mime_type
import nav.db
import psycopg2.extras


def geomap(request):
    return render_to_response(GeomapTemplate,
                              'geomap/geomap.html',
                              {},
                              RequestContext(request),
                              path=[('Home', '/'),
                                    ('Geomap', None)])

            
def data(request):
#    connection = nav.db.getConnection('netmapserver', 'manage')
    # TODO remove this (using teknobyen-vk temporarily for testing)
    connection = psycopg2.connect(nav.db.get_connection_string(('teknobyen-vk.uninett.no',
                                                                5432,
                                                                'nav',
                                                                'navread',
                                                                'bjcgpzQy6')))
    connection.set_isolation_level(1)
    db = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    format = request.GET['format']
    bounds = {'minLon': float(request.GET['minLon']),
              'maxLon': float(request.GET['maxLon']),
              'minLat': float(request.GET['minLat']),
              'maxLat': float(request.GET['maxLat'])}
    viewport_size = {'width': int(request.GET['viewportWidth']),
                     'height': int(request.GET['viewportHeight'])}
    limit = int(request.GET['limit'])

#     geojson = get_geojson(db, bounds, viewport_size, limit)

    data = get_formatted_data(db, format, bounds, viewport_size, limit)
    response = HttpResponse(data)
    response['Content-Type'] = format_mime_type(format)
    response['Content-Type'] = 'text/plain' # TODO remove this
    return response
