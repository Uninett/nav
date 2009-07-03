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

from django.template import Context, Template

import nav
from nav.web.geomap.conf import get_configuration
from nav.web.geomap.utils import *


_node_feature_properties = []
_edge_feature_properties = []

_place_popup_template = None
_network_popup_template = None


def create_features(graph):
    nodes = map(create_node_feature, graph.nodes.values())
    edges = concat_list(map(create_edge_features, graph.edges.values()))
    return nodes+edges


def template_from_config(filename):
    abs_filename = os.path.join(nav.path.sysconfdir, filename)
    file = open(abs_filename, 'r')
    content = file.read()
    file.close()
    return Template(content)


def load_place_popup_template():
    global _place_popup_template
    if _place_popup_template is None:
        _place_popup_template = \
            template_from_config('geomap/popup_place.html')


def load_network_popup_template():
    global _network_popup_template
    if _network_popup_template is None:
        _network_popup_template = \
            template_from_config('geomap/popup_network.html')


def apply_indicator(ind, type, properties):
    if type == ind['type']:
        for option in ind['options']:
            if eval(option['test'], properties):
                # TODO error handling
                return {ind['property']: option['value']}
    return {}


def apply_all_indicators(type, properties):
    return apply(union_dict,
                 map(lambda ind: apply_indicator(ind, type, properties),
                     get_configuration()['indicators']))


def create_node_feature(node):
    style = apply_all_indicators('node', node.properties)
    return Feature(node.id, 'node', Geometry('Point', [node.lon, node.lat]),
                   style['color'], style['size'], create_node_popup(node),
                   subdict(node.properties, _node_feature_properties))


def create_node_popup(node):
    load_place_popup_template()
    content = _place_popup_template.render(Context({'place': node}))
    return Popup('popup-' + node.id, [300,250], content, True)


def create_edge_features(edge):
    popup = create_edge_popup(edge)
    def make_feature(id_suffix, source_coords, target_coords, properties):
        style = apply_all_indicators('edge', properties)
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


def create_edge_popup(edge):
    load_network_popup_template()
    content = _network_popup_template.render(Context({'network': edge}))
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
