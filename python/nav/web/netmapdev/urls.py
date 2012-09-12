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


# The patterns are relative to the base URL of the subsystem
from nav.web.netmapdev.views import netmap, maps, \
    d3js_layer2, d3js_layer3, traffic_load_gradient, graphml_layer2, \
    backbone_app, netmap_defaultview, netmap_defaultview_global, admin_views

urlpatterns = patterns('nav.web.netmapdev.views',
    url(r'^$', backbone_app, name='netmapdev-index'),
    url(r'^admin$', admin_views, name='netmapdev-admin-views'),
    url(r'^api/netmap$', maps,
        name='netmapdev-api-netmap'),
    url(r'^api/netmap/defaultview$', netmap_defaultview_global,
        name='netmapdev-api-netmap-defaultview-global'),
    url(r'^api/netmap/(?P<map_id>[\d]+)$', netmap,
        name='netmapdev-api-netmap'),
    url(r'^api/netmap/user/defaultview$',
        netmap_defaultview,
        name='netmapdev-api-netmap-defaultview'),
    url(r'^api/graph/layer2$', d3js_layer2,
        name='netmapdev-api-graph-layer2'),
    url(r'^api/graph/layer2/(?P<map_id>[\d]+)$', d3js_layer2,
        name='netmapdev-api-graph-layer2-map'),
    url(r'^api/graph/layer3$', d3js_layer3,
        name='netmapdev-api-graph-layer3'),
    url(r'^api/graph/layer3/(?P<map_id>[\d]+)$', d3js_layer3,
        name='netmapdev-api-graph-layer3-map'),

    url(r'^api/traffic_load_gradient', traffic_load_gradient,
        name='netmapdev-api-traffic_load_gradient'),


    # old netmap, grapml format, meh meh.
    url(r'^data/graphml/layer2$', graphml_layer2,
        name='netmapdev-data-graphml-layer2'),


    #url(r'^data/views', get_views, name='netmapdev-get_views'),

)
