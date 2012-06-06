#
# Copyright (C) 2012 UNINETT AS
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
"""Netmap backend URL config."""

from django.conf.urls.defaults import url, patterns

from nav.web.netmapdev.views import demo, d3js_layer2, graphml_layer2, index, \
    graph_layer2_view2, graph_layer2_view1, \
    graph_layer2_view3, traffic_load_gradient, show_view, save_view_metadata

# The patterns are relative to the base URL of the subsystem
urlpatterns = patterns('nav.web.netmapdev.views',
    url(r'^$', index, name='netmapdev-index'),
    url(r'^graph/layer2/view1', graph_layer2_view1,
        name='netmapdev-graph-layer2-view1'),
    url(r'^graph/layer2/view2', graph_layer2_view2,
        name='netmapdev-graph-layer2-view2'),
    url(r'^graph/layer2/view3', graph_layer2_view3,
        name='netmapdev-graph-layer2-view3'),
    url(r'^data/graphml/layer2$', graphml_layer2,
        name='netmapdev-data-graphml-layer2'),
    url(r'^data/d3js/layer2$', d3js_layer2,
        name='netmapdev-data-d3js-layer2'),
    url(r'^data/d3js/layer2/(?P<view_id>[\w\d]+)$', d3js_layer2,
        name='netmapdev-data-d3js-layer2'),
    url(r'^data/traffic_load_gradient', traffic_load_gradient,
        name='netmapdev-data-traffic_load_gradient'),
    url(r'^v/(?P<view_id>[\w\d]+)$', show_view, name='netmapdev-showview'),
    url(r'^v/(?P<view_id>[\w\d]+)/save$', save_view_metadata,
        name='netmapdev-save_view_metadata'),
    url(r'^demo$', demo, name='netmapdev-demo'),
)
