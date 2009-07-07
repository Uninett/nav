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
from django import forms

from nav.django.shortcuts import render_to_response
import nav.db
import psycopg2.extras
from nav.web.geomap.conf import get_configuration
from nav.web.geomap.db import get_data, rrd_statistics
from nav.web.geomap.graph import build_graph, simplify
from nav.web.geomap.features import create_features
from nav.web.geomap.output_formats import format_data, format_mime_type
from nav.web.templates.GeomapTemplate import GeomapTemplate


class TimeIntervalForm(forms.Form):
    interval_size = forms.ChoiceField(
        [('10min', '10 minutes'),
         ('1hour', 'Hour'),
         ('1day', 'Day'),
         ('1week', 'Week')],
        required=False)
    endtime = forms.CharField(required=False, initial='now')


def geomap(request):
    if request.GET.has_key('endtime'):
        time_interval_form = TimeIntervalForm(request.GET)
    else:
        time_interval_form = TimeIntervalForm()
    return render_to_response(GeomapTemplate,
                              'geomap/geomap.html',
                              {'config': get_configuration(),
                               'time_interval_form': time_interval_form},
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

#     geojson = get_geojson(db, bounds, viewport_size, limit)

    #rrd_statistics['cache'] = 0
    #rrd_statistics['file'] = 0
    data = get_formatted_data(db, format, bounds, viewport_size, limit,
                              time_interval)
    #data = ('//cache: %d, file: %d\n' % (rrd_statistics['cache'], rrd_statistics['file'])) + data
    response = HttpResponse(data)
    response['Content-Type'] = format_mime_type(format)
    response['Content-Type'] = 'text/plain' # TODO remove this
    return response


def get_formatted_data(db, format, bounds, viewport_size, limit,
                       time_interval):
    """Get formatted output for given conditions.

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
    graph = build_graph(get_data(db, bounds, time_interval))
    simplify(graph, bounds, viewport_size, limit)
    features = create_features(graph)
    return format_data(format, features)
