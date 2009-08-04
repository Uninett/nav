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

"""Formatting of data. Supported formats: GeoJSON, KML.

See
http://geojson.org/geojson-spec.html
http://code.google.com/apis/kml/

"""


from django.template.loader import render_to_string

from nav.web.geomap.utils import *

# GeoJSON:

def make_geojson(featurelist):
    """Create a GeoJSON representation of a list of features."""
    geojson = {'type': 'FeatureCollection',
               'features': map(make_geojson_feature, featurelist)}
    return write_json(geojson)

def make_geojson_feature(feature):
    """Create a GeoJSON object for a feature."""
    popup = None
    if feature.popup:
        popup = {'id': feature.popup.id,
                 'size': feature.popup.size,
                 'content': feature.popup.content,
                 'closable': feature.popup.closable}
    return {'type': 'Feature',
            'id': feature.id,
            'geometry':
                {'type': feature.geometry.type,
                 'coordinates': feature.geometry.coordinates},
            'properties':
                union_dict({'type': feature.type,
                            'color': feature.color,
                            'size': feature.size,
                            'popup': popup},
                           feature.properties)}

# should use json.dumps, but navdev has too old Python version
json_escapes = [('\\', '\\\\'),
                ('"', '\\"'),
                ('\n', '\\n'),
                ('\r', '\\r')]

def write_json(obj):
    """Convert an object to a JSON string.

    Dictionaries, lists, strings, numbers, booleans and None are
    recognized and represented as JSON values in the obvious way. The
    occurence of objects of any other type in obj is an error.

    This function is only needed in pre-2.6 versions of Python. From
    version 2.6, it may be replaced by the standard library's
    json.dumps.

    """
    if isinstance(obj, list):
        return '[' + ', '.join(map(write_json, obj)) + ']'
    if isinstance(obj, dict):
        return '{' + ', '.join(map(lambda kv: kv[0]+':'+kv[1],
                                   zip(map(write_json, obj.keys()),
                                       map(write_json, obj.values())))) + '}'
    if isinstance(obj, bool):
        if obj: return 'true'
        return 'false'
    if isinstance(obj, basestring):
        return '"%s"' % reduce(lambda s,esc: s.replace(esc[0], esc[1]),
                               json_escapes, obj)
    if numeric(obj):
        return str(obj)
    if obj == None:
        return 'null'
    return '"ERROR: unrecognized type ' + str(type(obj)) + '"'



# KML

def make_kml(featurelist):
    return render_to_string('geomap/geomap-data-kml.xml',
                            {'features': featurelist})



# General

_formats = {
    'geojson': (make_geojson, 'application/json'),
    'kml': (make_kml, 'application/vnd.google-earth.kml+xml')
    };

def format_data(format, featurelist):
    """Format features in featurelist to a string.

    Arguments:

    format -- name of a format (key in _formats)

    featurelist -- list of features

    """
    if not format in _formats:
        raise Exception('unknown format %s' % format)
    formatter = _formats[format][0]
    return formatter(featurelist)

def format_mime_type(format):
    """Returns the MIME type for the specified format."""
    if not format in _formats:
        raise Exception('unknown format %s' % format)
    return _formats[format][1]



