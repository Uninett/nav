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


"""

import os
import logging

from django.template import Context, Template

import nav
from nav.web.geomap.conf import get_configuration
from nav.web.geomap.utils import *


logger = logging.getLogger('nav.web.geomap.features')

_node_feature_properties = []
_edge_feature_properties = []


def create_features(variant, graph):
    variant_config = get_configuration()['variants'][variant]
    indicators = variant_config['indicators']
    styles = variant_config['styles']
    template_files = variant_config['template_files']
    node_popup_template = template_from_config(template_files['node_popup'])
    edge_popup_template = template_from_config(template_files['edge_popup'])

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


def template_from_config(filename):
    if filename is None:
        return None
    confdir = os.path.join(nav.path.sysconfdir, 'geomap')
    abs_filename = os.path.join(confdir, filename)
    file = open(abs_filename, 'r')
    content = file.read()
    file.close()
    return Template(content)


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
    for option in ind['options']:
        try:
            # Properties must be passed as locals, not globals,
            # since it may not be a dict object (we use lazy_dict
            # from utils.py). (See documentation of eval).
            test_result = eval(option['test'], {}, properties)
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
    return apply(union_dict,
                 map(fix(apply_indicator, properties, 1), indicators))

# def apply_all_indicators(type, properties):
#     return apply(union_dict,
#                  map(lambda ind: apply_indicator(ind, type, properties),
#                      get_configuration()['indicators']))


def create_node_feature(node, popup_template, default_style, indicators):
    style = union_dict(default_style,
                       apply_indicators(indicators, node.properties))
    return Feature(node.id, 'node', Geometry('Point', [node.lon, node.lat]),
                   style['color'], style['size'],
                   create_node_popup(node, popup_template),
                   subdict(node.properties, _node_feature_properties))


def create_node_popup(node, popup_template):
    if popup_template is None:
        return None
    content = popup_template.render(Context({'place': node}))
    return Popup('popup-' + node.id, [300,250], content, True)


def create_edge_features(edge, popup_template, default_style, indicators):
    popup = create_edge_popup(edge, popup_template)
    def make_feature(id_suffix, source_coords, target_coords, properties):
        style = union_dict(default_style,
                           apply_indicators(indicators, properties))
        return Feature(str(edge.id)+id_suffix, 'edge',
                       Geometry('LineString', [source_coords, target_coords]),
                       style['color'], style['size'], popup,
                       subdict(properties, _edge_feature_properties))

    properties = subdict(edge.properties, _edge_feature_properties)
    properties_forward = union_dict(edge.properties,
                                    {'load': edge.properties['load_in']})
    properties_back = union_dict(edge.properties,
                                 {'load': edge.properties['load_out']})
    source = [edge.source.lon, edge.source.lat]
    middle = [(edge.source.lon+edge.target.lon)/2,
              (edge.source.lat+edge.target.lat)/2]
    target = [edge.target.lon, edge.target.lat]
    return [make_feature('[1]', source, middle, properties_forward),
            make_feature('[2]', middle, target, properties_back)]


def create_edge_popup(edge, popup_template):
    if popup_template is None:
        return None
    content = popup_template.render(Context({'network': edge}))
    return Popup('popup-' + edge.id, [300,250], content, True)
    

class Feature:
    def __init__(self, id, type, geometry, color, size, popup, properties):
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
