#
# Copyright (C) 2007, 2010, 2011 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Netmap mod_python handler"""

import psycopg2.extras

from django.template import RequestContext
from django.http import HttpResponse
from django.utils import simplejson

from nav.django.shortcuts import render_to_response

from nav.topology import vlan
from nav.topology.d3_js import d3_json

from nav.web.netmapdev.common import layer2_graph, traffic_gradient_map
from nav.web.templates.Netmapdev import Netmapdev

import networkx as nx

def index(request):
    return graph_layer2_view2(request)


def demo(request):
    """d3js force-layout graph demo."""
    return render_to_response(Netmapdev,
        'netmapdev/demo.html',
            {
        },
        RequestContext(request),
        path=[('Home', '/'),
            ('Netmapdev', None)])


def graph_layer2_view1(request):
    return render_to_response(Netmapdev,
        'netmapdev/index.html',
            {'data': 'd3js/layer2',
             },
        RequestContext(request),
        path=[('Home', '/'),
            ('Netmapdev', None)])


def graph_layer2_view2(request):
    return render_to_response(Netmapdev,
        'netmapdev/force_direct.html',
            {'data': 'd3js/layer2',
             },
        RequestContext(request),
        path=[('Home', '/'),
            ('Netmapdev', None)])

def graph_layer2_view3(request):
    return render_to_response(Netmapdev,
        'netmapdev/force_direct_2.html',
            {'data': 'd3js/layer2',
             },
        RequestContext(request),
        path=[('Home', '/'),
            ('Netmapdev', None)])


# data views, graphml

def graphml_layer2(request):
    """Layer2 network topology representation in graphml format."""

    netboxes, connections = layer2_graph()

    response = render_to_response(Netmapdev,
        'netmapdev/graphml.html',
            {'netboxes': netboxes,
             'connections': connections,
             'layer': 2,
             },
        RequestContext(request),
        path=[
            ('Home', '/'),
            ('Netmapdev', None)
        ],
    )
    response['Content-Type'] = 'application/xml; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response

# data views, d3js

def d3js_layer2(request):
    """
    Layer2 network topology representation in d3js force-direct graph layout
    http://mbostock.github.com/d3/ex/force.html
    """
    json = json_layer2()
    json['colormap']=traffic_gradient_map()
    response = HttpResponse(simplejson.dumps(json))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response


def json_layer2():
    graph = vlan.build_layer2_graph().to_undirected()
    return d3_json(graph, None)


def traffic_load_gradient(request):
    response = HttpResponse(simplejson.dumps(traffic_gradient_map()))
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response

def show_view(request, view_id):
    return HttpResponse(view_id)

def save_view_metadata(request, view_id):
    return HttpResponse(view_id)