#
# Copyright (C) 2009, 2010 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License version 3 as published by the Free
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

import json
from django.template.loader import render_to_string

# GeoJSON:


def make_geojson(featurelist):
    """Create the GeoJSON representation of a list of features.

    The result is a GeoJSON string.

    """
    geojson = {
        'type': 'FeatureCollection',
        'features': [make_geojson_feature(f) for f in featurelist],
    }
    return json.dumps(geojson)


def make_geojson_feature(feature):
    """Create a GeoJSON object for a feature."""
    popup = None
    if feature.popup:
        popup = {
            'id': feature.popup.id,
            'size': feature.popup.size,
            'content': feature.popup.content,
            'closable': feature.popup.closable,
        }
    properties = {
        'type': feature.type,
        'color': feature.color,
        'size': feature.size,
        'popup': popup,
    }
    properties.update(feature.properties)
    return {
        'type': 'Feature',
        'id': feature.id,
        'geometry': {
            'type': feature.geometry.type,
            'coordinates': feature.geometry.coordinates,
        },
        'properties': properties,
    }


# KML


def make_kml(featurelist):
    return render_to_string('geomap/geomap-data-kml.xml', {'features': featurelist})


# General


_formats = {
    'geojson': (make_geojson, 'application/json'),
    'kml': (make_kml, 'application/vnd.google-earth.kml+xml'),
}


def format_data(format, featurelist):
    """Format features in featurelist to a string.

    Arguments:

    format -- name of a format (key in _formats)

    featurelist -- list of features

    """
    if format not in _formats:
        raise Exception('unknown format %s' % format)
    formatter = _formats[format][0]
    return formatter(featurelist)


def format_mime_type(format):
    """Returns the MIME type for the specified format."""
    if format not in _formats:
        raise Exception('unknown format %s' % format)
    return _formats[format][1]
