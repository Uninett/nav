#
# Copyright (C) 2009, 2010 UNINETT AS
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

"""Views for Geomap."""


import logging
import psycopg2.extras
from decimal import Decimal

from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from django.core.urlresolvers import reverse
from django import forms

import nav.db
from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account

from nav.web.geomap.conf import get_configuration
from nav.web.geomap.db import get_data
from nav.web.geomap.db import get_data_finish
from nav.web.geomap.graph import build_graph
from nav.web.geomap.graph import simplify
from nav.web.geomap.features import create_features
from nav.web.geomap.output_formats import format_data
from nav.web.geomap.output_formats import format_mime_type
from nav.web.templates.GeomapTemplate import GeomapTemplate

from nav.models.manage import Room

logger = logging.getLogger('nav.web.geomap.views')

DEFAULT_LON = Decimal('10.4059409151806')
DEFAULT_LAT = Decimal('63.4141131037476')

DEFAULT_VARIANCE = Decimal('0.5')

def geomap_get_lat_lon():
    lon = DEFAULT_LON
    lat = DEFAULT_LAT
    sum_lon = Decimal(0)
    sum_lat = Decimal(0)
    rooms_with_pos = Room.objects.filter(position__isnull=False)
    if len(rooms_with_pos) > 0:
        num_pos = len(rooms_with_pos)
        for room in rooms_with_pos:
            room_lat, room_lon = room.position
            sum_lon += room_lon
            sum_lat += room_lat
        lon = sum_lon / num_pos
        lat = sum_lat / num_pos
    return (float(lon), float(lat))
        
def geomap_bbox():
    max_lon = Decimal(0)
    min_lon = Decimal(2147483647L)
    max_lat = Decimal(0)
    min_lat = Decimal(2147483647L)
    bbox = (float(DEFAULT_LON - DEFAULT_VARIANCE),
            float(DEFAULT_LAT - DEFAULT_VARIANCE),
            float(DEFAULT_LON + DEFAULT_VARIANCE),
            float(DEFAULT_LAT + DEFAULT_VARIANCE))
    rooms_with_pos = Room.objects.filter(position__isnull=False)
    if len(rooms_with_pos) > 0:
        for room in rooms_with_pos:
            room_lat, room_lon = room.position
            if room_lon > max_lon:
                max_lon = room_lon
            if room_lon < min_lon:
                min_lon = room_lon
            if room_lat > max_lat:
                max_lat = room_lat
            if room_lat < min_lat:
                min_lat = room_lat
        bbox = (float(min_lon), float(min_lat), float(max_lon), float(max_lat))
    return bbox

def geomap(request, variant):
    """Create the page showing the map.

    variant must be a variant name defined in the configuration file.

    """
    config = get_configuration()
    if variant not in config['variants']:
        raise Http404
    start_lon, start_lat = geomap_get_lat_lon()
    lon_1, lat_1, lon_2, lat_2 = geomap_bbox()
    logger.error('geomap: start_lon = %f, start_lat = %f' %
                                (start_lon, start_lat))
    logger.error('geomap: lon_1 = %f, lat_1 = %f, lon_2 = %f, lat_2 = %f' %
                    (lon_1, lat_1, lon_2, lat_2))
    variant_config = config['variants'][variant]
    return render_to_response(GeomapTemplate,
                              'geomap/geomap.html',
                              {'start_lon': start_lon,
                               'start_lat': start_lat,
                               'lon_1': lon_1,
                               'lat_1': lat_1,
                               'lon_2': lon_2,
                               'lat_2': lat_2,
                               'config': config,
                               'variant': variant,
                               'variant_config': variant_config},
                              RequestContext(request),
                              path=[('Home', '/'),
                                    ('Geomap', None)])

            
def forward_to_default_variant(request):
    """Redirect the client to the default variant.

    The default variant is the one listed first in the configuration
    file.

    """
    account = get_account(request)
    for variant in get_configuration()['variant_order']:
        url = reverse('geomap', args=(variant,))
        if account.has_perm('web_access', url):
            return HttpResponseRedirect(url)
    return HttpResponseForbidden # TODO: should use 'Unauthorized'


def data(request, variant):
    """Respond to a data request.

    GET paramaters in the request object specify the bounding box of
    the area to retrieve data for and other parameters.

    variant must be a variant name defined in the configuration file.

    """
    connection = nav.db.getConnection('geomapserver', 'manage')
    connection.set_isolation_level(1)
    db = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    format = request.GET['format']
    if request.GET.has_key('bbox'):
        bbox = request.GET['bbox']
        bounds = {}
        (bounds['minLon'], bounds['minLat'],
         bounds['maxLon'], bounds['maxLat']) = map(float, bbox.split(','))
    else:
        bounds = {'minLon': float(request.GET['minLon']),
                  'maxLon': float(request.GET['maxLon']),
                  'minLat': float(request.GET['minLat']),
                  'maxLat': float(request.GET['maxLat'])}
    viewport_size = {'width': int(request.GET['viewportWidth']),
                     'height': int(request.GET['viewportHeight'])}
    limit = int(request.GET['limit'])
    if request.GET.has_key('timeStart') and request.GET.has_key('timeEnd'):
        time_interval = {'start': request.GET['timeStart'],
                         'end': request.GET['timeEnd']}
    else:
        time_interval = None

    data = get_formatted_data(variant, db, format, bounds, viewport_size,
                              limit, time_interval)
    response = HttpResponse(data)
    response['Content-Type'] = format_mime_type(format)
    response['Content-Type'] = 'text/plain' # TODO remove this
    return response


def get_formatted_data(variant, db, format, bounds, viewport_size, limit,
                       time_interval):
    """Get formatted output for given conditions.

    variant -- name of the map variant to create data for (variants
    are defined in the configuration file)

    db -- a database connection object.

    format -- the name of a format (see output_formats.py)

    bounds -- a dictionary with keys (minLon, maxLon, minLat, maxLat)
    describing the bounds of the interesting region.

    viewport_size -- a dictionary with keys (width, height), the width
    and height of the user's viewport for the map in pixels.

    limit -- the minimum distance (in pixels) there may be between two
    points without them being collapsed to one.

    time_interval -- dictionary with keys ('start', 'end'). Values
    should be strings describing times in the syntax expected by
    rrdfetch. (see http://oss.oetiker.ch/rrdtool/doc/rrdfetch.en.html)

    Return value: formatted data as a string.

    """
    logger.debug('get_data')
    data = get_data(db, bounds, time_interval)
    logger.debug('build_graph')
    graph = build_graph(data)
    logger.debug('simplify')
    simplify(graph, bounds, viewport_size, limit)
    logger.debug('create_features')
    features = create_features(variant, graph)
    logger.debug('format')
    output = format_data(format, features)
    get_data_finish()
    return output
