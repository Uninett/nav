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
import datetime
import logging
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404

from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, \
    HttpResponseRedirect, HttpResponseBadRequest
from django.utils import simplejson
from nav.models.manage import Netbox

from nav.models.profiles import Account, NetmapView, NetmapViewNodePosition

from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account


from nav.topology import vlan
from nav.topology.d3_js import d3_json

from nav.web.netmapdev.common import layer2_graph, traffic_gradient_map, \
    edge_to_json, attach_rrd_data_to_edges, build_netmap_layer2_graph
from nav.web.netmapdev.forms import ViewSaveForm, NewViewSaveForm
from nav.web.templates.Netmapdev import Netmapdev

import networkx as nx

_LOGGER = logging.getLogger('nav.web.netmapdev.views')


def index(request):
    return graph_layer2_view2(request, get_account(request) )


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


def graph_layer2_view2(request, user=None, view=None):
    views = NetmapView.objects.filter(Q(is_public=True) | Q(owner=user.id))\
        .order_by('-is_public')


    # 'netmapdev/force_direct.html',
    response = render_to_response(Netmapdev,
        'netmapdev/view.html',
            {'data': 'd3js/layer2',
             'current_view': view,
             'views': views,
             },
        RequestContext(request),
        path=[('Home', '/'),
            ('Netmapdev', None)])
    if view:
        response['x-nav-viewid'] = view.pk
    return response

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

def d3js_layer2(request, view_id=None):
    """
    Layer2 network topology representation in d3js force-direct graph layout
    http://mbostock.github.com/d3/ex/force.html
    """
    if view_id:
        view = get_object_or_404(NetmapView, pk=view_id)
        if view.is_public or (session_user == view.owner):
            json = json_layer2(view)
            json['colormap']=traffic_gradient_map()
            response = HttpResponse(simplejson.dumps(json))
            response['Content-Type'] = 'application/json; charset=utf-8'
            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
            response['x-nav-viewid'] = view_id
            return response
        else:
            return HttpResponseForbidden()

    json = json_layer2()
    json['colormap']=traffic_gradient_map()
    response = HttpResponse(simplejson.dumps(json))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response

def json_layer2(view=None):
    graph = nx.Graph(build_netmap_layer2_graph(view))
    return d3_json(graph, None)

def test_traffic_foo(request):
    _LOGGER.debug("netmap:test_traffic_foo() start")
    graph = build_netmap_layer2_graph()
    _LOGGER.debug("netmap:test_traffic_foo() graph done")
    ints_graph = nx.convert_node_labels_to_integers(graph, discard_old_labels=False)
    _LOGGER.debug("netmap:test_traffic_foo() base convert done")
    json_edges = list()
    for j, k, w in ints_graph.edges_iter(data=True):
        e = {'source': j, 'target': k,
             'data': edge_to_json(w['metadata']), 'value': 1}
        json_edges.append(e)
    _LOGGER.debug("netmap:test_traffic_foo() edges done - starting RRD")
    json_edges  = attach_rrd_data_to_edges(ints_graph, json_edges, True)
    _LOGGER.debug("netmap:test_traffic_foo() rrd done")
    response = HttpResponse(simplejson.dumps(json_edges))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response

def traffic_load_gradient(request):
    response = HttpResponse(simplejson.dumps(traffic_gradient_map()))
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response

def _get_views(session_user):
    views = NetmapView.objects.filter(Q(is_public=True) | Q(owner=session_user.id))\
        .order_by('-is_public')
    return views

def get_views(request):
    session_user = get_account(request)

    response = HttpResponse(simplejson.dumps(_get_views(session_user)))
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response

def show_view(request, view_id):
    view =  get_object_or_404(NetmapView, pk=view_id)
    session_user = get_account(request)

    if view.is_public or (session_user == view.owner):
        # render right view with properties from netmapview,
        # netmapview categories etc.

        return graph_layer2_view2(request, session_user, view) #
    else:
        return graph_layer2_view2(request, session_user) # default view
    return HttpResponse(view_id)

def save_new_view(request):
    if request.method == 'POST':
        form = NewViewSaveForm(request.POST)

        session_user = get_account(request)

        if form.is_valid():
            view = NetmapView()
            view.owner = session_user
            view.title = form.cleaned_data['title']
            view.link_types = form.cleaned_data['link_types']
            view.zoom = form.cleaned_data['zoom']
            view.is_public= form.cleaned_data['is_public']
            view.last_modified = datetime.datetime.now()
            if form.cleaned_data['fixed_nodes']:
                fixed_nodes = simplejson.loads(form
                                               .cleaned_data['fixed_nodes'])
            view.save()

            for i in fixed_nodes:
                a_node = i

                view = NetmapView.objects.get(pk=view.pk)
                netbox = Netbox.objects.get(pk=a_node['data']['id'])

                NetmapViewNodePosition.objects.create(
                    viewid=view,
                    netbox=netbox,
                    x=a_node['x'],
                    y=a_node['y'])

            #response = HttpResponse(simplejson.dumps({
            #    'current_view': view,
            #    'views': _get_views(session_user),
            #}))
            #response['Content-Type'] = 'application/json; charset=utf-8'
            #return response
            return HttpResponseRedirect(reverse(show_view,
                args=[view.pk]))
    return HttpResponseBadRequest()


def save_view_metadata(request, view_id):
    view =  get_object_or_404(NetmapView, pk=view_id)
    session_user = get_account(request)



    if session_user == view.owner and request.method == 'POST':
        form = ViewSaveForm(request.POST)

        if form.is_valid():
            if form.cleaned_data['title']:
                view.title = form.cleaned_data['title']
            if form.cleaned_data['link_types']:
                view.link_types = form.cleaned_data['link_types']
            if form.cleaned_data['zoom']:
                view.zoom = form.cleaned_data['zoom']
            if form.cleaned_data['is_public']:
                view.is_public= form.cleaned_data['is_public']
            view.last_modified = datetime.datetime.now()
            if form.cleaned_data['fixed_nodes']:
                fixed_nodes = simplejson.loads(form
                                               .cleaned_data['fixed_nodes'])

                NetmapViewNodePosition.objects.filter(viewid=view.pk).delete()
                for i in fixed_nodes:
                    a_node = i

                    view = NetmapView.objects.get(pk=view.pk)
                    netbox = Netbox.objects.get(pk=a_node['data']['id'])

                    NetmapViewNodePosition.objects.create(
                        viewid=view,
                        netbox=netbox,
                        x=a_node['x'],
                        y=a_node['y'])

            logger.debug('updating view metadata: %s' % view)

            view.save()

            #response = HttpResponse(simplejson.dumps({
            #    'current_view': view,
            #    'views': _get_views(session_user),
            #    }))
            #response['Content-Type'] = 'application/json; charset=utf-8'
            #return response
            return HttpResponseRedirect(reverse(show_view,
                args=[view.pk]))
        return HttpResponseBadRequest()


    else:
        return HttpResponseForbidden()
