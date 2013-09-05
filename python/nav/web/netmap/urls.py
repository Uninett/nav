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
from nav.web.netmap.views import (netmap, maps,
                                  api_graph_layer_2, api_graph_layer_3,
                                  traffic_load_gradient, graphml_layer2,
                                  backbone_app, netmap_defaultview,
                                  netmap_defaultview_global, admin_views,
                                  api_datauris_categories)

urlpatterns = patterns('nav.web.netmap.views',
    url(r'^$', backbone_app, name='netmap-index'),
    url(r'^admin$', admin_views, name='netmap-admin-views'),
    url(r'^api/netmap$', maps,
        name='netmap-api-netmap'),
    url(r'^api/netmap/defaultview$', netmap_defaultview_global,
        name='netmap-api-netmap-defaultview-global'),
    url(r'^api/netmap/(?P<map_id>[\d]+)$', netmap,
        name='netmap-api-netmap'),
    url(r'^api/netmap/defaultview/user$',
        netmap_defaultview,
        name='netmap-api-netmap-defaultview'),
    url(r'^api/graph/layer2$', api_graph_layer_2,
        name='netmap-api-graph-layer2'),
    url(r'^api/graph/layer2/(?P<map_id>[\d]+)$', api_graph_layer_2,
        name='netmap-api-graph-layer2-map'),
    url(r'^api/graph/layer3$', api_graph_layer_3,
        name='netmap-api-graph-layer3'),
    url(r'^api/graph/layer3/(?P<map_id>[\d]+)$', api_graph_layer_3,
        name='netmap-api-graph-layer3-map'),

    url(r'^api/traffic_load_gradient', traffic_load_gradient,
        name='netmap-api-traffic_load_gradient'),
    url(r'^api/data_uris_categories', api_datauris_categories,
        name='netmap-api-data_uris_categories'),

    # old netmap, grapml format, meh meh.
    url(r'^data/graphml/layer2$', graphml_layer2,
        name='netmap-data-graphml-layer2'),



)
