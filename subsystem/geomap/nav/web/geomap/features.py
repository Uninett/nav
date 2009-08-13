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

"""Create points, lines and popups based on a graph.

The terminology (in particular, the words 'feature' and 'geometry')
and data representation used in this module are based on GeoJSON[1].

A _feature_ is a point or a line. A feature has an associated
_geometry_, which specifies the type ('Point' or 'LineString') and
coordinates of the feature. A feature also has a color and a size, and
a popup box (these are our own additions, not from GeoJSON). A feature
also has a set of properties, which are arbitrary key/value pairs.

___

1: http://geojson.org/geojson-spec.html

"""

import os
import logging

from django.template import Context, Template
from django import template

import nav
from nav.web.geomap.conf import get_configuration
from nav.web.geomap.utils import *


logger = logging.getLogger('nav.web.geomap.features')

_node_feature_properties = []
_edge_feature_properties = []


def create_features(variant, graph):
    """Create features (points/lines) and popups from a graph."""
    variant_config = get_configuration()['variants'][variant]
    indicators = variant_config['indicators']
    styles = variant_config['styles']
    template_files = variant_config['template_files']
    node_popup_template = load_popup_template(template_files['node_popup'])
    edge_popup_template = load_popup_template(template_files['edge_popup'])

    node_feature_creator = fix(create_node_feature,
                               [node_popup_template, styles['node'],
                                indicators['node']],
                               1)
    edge_feature_creator = fix(create_edge_features,
                               [edge_popup_template, styles['edge'],
                                indicators['edge']],
                               1)

    nodes = map(node_feature_creator, graph.nodes.values())
    edges = concat_list(map(edge_feature_creator, graph.edges.values()))
    return nodes+edges


def filter_nan2none(value):
    """Convert the NaN value to None, leaving everything else unchanged.

    This function is meant to be used as a Django template filter. It
    is useful in combination with filters that handle None (or any
    false value) specially, such as the 'default' filter, when one
    wants special treatment for the NaN value. It is also useful
    before the 'format' filter to avoid the NaN value being formatted.

    """
    if is_nan(value):
        return None
    return value


def filter_format(value, arg):
    """Format value according to format string arg.

    This function is meant to be used as a Django template filter.

    """
    try:
        return arg % value
    except:
        return ''


def load_popup_template(filename):
    """Load the template for a popup.

    Returns a django.template.Template object.

    """
    filters = {'nan2none': filter_nan2none,
               'format': filter_format}
    return template_from_config(filename, filters)


def template_from_config(filename, filters={}):
    """Create a Django template from a configuration file.

    Arguments:

    filename -- name of configuration file containing template
    (relative to the geomap configuration directory)

    filters -- additional template filters (see
    compile_template_with_filters)

    """
    if filename is None:
        return None
    confdir = os.path.join(nav.path.sysconfdir, 'geomap')
    abs_filename = os.path.join(confdir, filename)
    file = open(abs_filename, 'r')
    content = file.read()
    file.close()
    return compile_template_with_filters(content, filters)


def compile_template_with_filters(template_string, filters):
    """Compile a Django template, using additional filters.

    This is like Template(template_string) except that additional
    filters to be made available to the template may be specified.

    Normally, one would define filters as documented in [1], but this
    requires the INSTALLED_APPS settings to be set, which is not the
    case in NAV[2]. This function is just a hack to get around that
    limitation. The code is based on
    django.template.compile_string[3].

    filters should be a dictionary mapping filter names to functions.

    [1]: http://docs.djangoproject.com/en/dev/howto/custom-template-tags/
    [2]: http://metanav.uninett.no/devel:django_introduction#settings
    [3]: http://code.djangoproject.com/browser/django/trunk/django/template/__init__.py

    """
    lib = template.Library()
    for name in filters.keys():
        lib.filter(name, filters[name])
    lexer = template.Lexer(template_string, None)
    parser = template.Parser(lexer.tokenize())
    parser.add_library(lib)
    return parser.parse()


# def load_place_popup_template():
#     global _place_popup_template
#     if _place_popup_template is None:
#         _place_popup_template = \
#             template_from_config('geomap/popup_place.html')


# def load_network_popup_template():
#     global _network_popup_template
#     if _network_popup_template is None:
#         _network_popup_template = \
#             template_from_config('geomap/popup_network.html')


def apply_indicator(ind, properties):
    """Apply an indicator to a list of properties.

    The indicator specifies how to select a value for some style
    property based on the properties. It contains a list of possible
    values, each combined with a test expression which determines
    whether it should be selected. Each test expression is evaluated
    with properties as environment.

    The result is a single-item dictionary with the style property
    controlled by the indicator mapped to the computed value.

    """
    for option in ind['options']:
        try:
            # Properties must be passed as locals, not globals, since
            # it may not be a dict object (we use lazy_dict from
            # utils.py). (See documentation of eval).
            #
            # Besides, we need to send the current globals() as
            # globals in order to make our functions available to the
            # configuration file (this is of course dangerous, since
            # it allows the configuration file to do all kinds of
            # nasty stuff, but it is also quite useful).
            test_result = eval(option['test'], globals(), properties)
        except Exception, e:
            logger.warning(('Exception when evaluating test "%s" ' +
                            'for indicator "%s" on properties %s: %s') %
                           (option['test'], ind['name'], properties, e))
            continue
        if test_result:
            return {ind['property']: option['value']}
    logger.warning('No tests in indicator %s matched properties %s' %
                   (ind['name'], properties))


def apply_indicators(indicators, properties):
    """Apply a list of indicators to a list of properties."""
    return apply(union_dict,
                 map(fix(apply_indicator, properties, 1), indicators))

# def apply_all_indicators(type, properties):
#     return apply(union_dict,
#                  map(lambda ind: apply_indicator(ind, type, properties),
#                      get_configuration()['indicators']))


def create_node_feature(node, popup_template, default_style, indicators):
    """Create a feature representing a node.

    Arguments:

    node -- Node object (see graph.py)

    popup_template -- template for the contents of the popup

    default_style -- style values to use for properties which have no
    indicator

    indicators -- specifications of style properties based on
    properties of the node

    """
    style = union_dict(default_style,
                       apply_indicators(indicators, node.properties))
    return Feature(node.id, 'node', Geometry('Point', [node.lon, node.lat]),
                   style['color'], style['size'],
                   create_node_popup(node, popup_template),
                   subdict(node.properties, _node_feature_properties))


def create_node_popup(node, popup_template):
    """Create the popup for a node."""
    if popup_template is None:
        return None
    content = popup_template.render(Context({'place': node.properties}))
    return Popup('popup-' + node.id, [300,250], content, True)


def create_edge_features(edge, popup_template, default_style, indicators):
    """Create features representing an edge.

    Each edge is represented by _two_ features: one for each
    direction. Both features are lines; each goes from one endpoint of
    the edge to the point halfway between the endpoints. When applying
    indicators, an additional property 'load' is supplied, with value
    taken from 'load_in'/'load_out' depending on the direction.

    The popup is the same for both features.

    Return value: List of two features.

    Arguments:

    edge -- an Edge object (see graph.py)

    popup_template -- template for the contents of the popup

    default_style -- style values to use for properties which have no
    indicator

    indicators -- specifications of style properties based on
    properties of the edge

    """
    def make_feature(source_coords, target_coords, data):
        style = union_dict(default_style,
                           apply_indicators(indicators, data))
        popup = create_edge_popup(data, popup_template)
        return Feature(data['id'], 'edge',
                       Geometry('LineString', [source_coords, target_coords]),
                       style['color'], style['size'], popup)

    source = [edge.source.lon, edge.source.lat]
    middle = [(edge.source.lon+edge.target.lon)/2,
              (edge.source.lat+edge.target.lat)/2]
    target = [edge.target.lon, edge.target.lat]
    return [make_feature(source, middle, edge.sourceData),
            make_feature(middle, target, edge.targetData)]


def create_edge_popup(data, popup_template):
    """Create the popup for a node."""
    if popup_template is None:
        return None
    content = popup_template.render(Context({'network': data}))
    return Popup('popup-' + data['id'], [300,250], content, True)
    

class Feature:
    def __init__(self, id, type, geometry, color, size, popup, properties={}):
        self.id = id
        self.type = type
        self.geometry = geometry
        self.color = color
        self.size = size
        self.popup = popup
        self.properties = properties


class Geometry:
    def __init__(self, type, coordinates):
        self.type = type
        self.coordinates = coordinates
        

class Popup:
    def __init__(self, id, size, content, closable):
        self.id = id
        self.size = size
        self.content = content
        self.closable = closable
