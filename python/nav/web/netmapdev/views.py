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

import datetime
import logging
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404

from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden, \
    HttpResponseRedirect, HttpResponseBadRequest
from django.utils import simplejson



import networkx as nx
from nav.django.shortcuts import render_to_response
from nav.django.utils import get_account
from nav.models.manage import Netbox, Category
from nav.models.profiles import NetmapView, NetmapViewNodePosition, \
    NetmapViewCategories
from nav.netmap.topology import build_netmap_layer3_graph, \
    build_netmap_layer2_graph
from nav.topology.d3_js.d3_js import d3_json_layer2, d3_json_layer3
from nav.web.netmapdev.common import traffic_gradient_map, layer2_graph
from nav.web.templates import Netmapdev

_LOGGER = logging.getLogger('nav.web.netmapdev')


def index(request):
    return backbone_app(request, get_account(request) )


def backbone_app(request):
    response = render_to_response(Netmapdev,
        'netmapdev/backbone.html',
            {},
        RequestContext(request),
        path=[('Home', '/'),
            ('Netmapdev', None)])

    return response


# data views, d3js

def map(request, map_id):
    if request.method == 'PUT' or ('HTTP_X_HTTP_METHOD_OVERRIDE' in request.META and
                                   request.META['HTTP_X_HTTP_METHOD_OVERRIDE']=='PUT'):
        return update_map(request, map_id)
    elif request.method == 'GET':
        return get_map(request, map_id)
    else:
        return HttpResponseBadRequest()


def _update_map_node_positions(fixed_nodes, view):
    NetmapViewNodePosition.objects.filter(viewid=view.pk).delete()
    for i in fixed_nodes:
        a_node = i

        netbox = Netbox.objects.get(pk=a_node['data']['id'])
        NetmapViewNodePosition.objects.create(
            viewid=view,
            netbox=netbox,
            x=a_node['x'],
            y=a_node['y'])


def _update_map_categories(categories, view):
    """ todo django 1.4
    https://docs.djangoproject.com/en/dev/ref/models/querysets/#django.db.models.query.QuerySet.bulk_create
    https://docs.djangoproject.com/en/dev/releases/1.4/
    https://code.djangoproject.com/ticket/7596
    """
    NetmapViewCategories.objects.filter(view=view.pk).delete()
    for category in categories:
        if category != 'ELINK':
            category_model = Category.objects.get(pk=category)

            NetmapViewCategories.objects.create(
                view=view,
                category=category_model)



def update_map(request, map_id):
    view = get_object_or_404(NetmapView, pk=map_id)
    session_user = get_account(request)

    if view.is_public or (session_user == view.owner):
        # todo: change to request.PUT when swapping to mod_wsgi!

        try:
            # request.POST['model']
            # change to request.body when swapping to django >=1.4
            data = simplejson.loads(request.raw_post_data)
        except KeyError:
            return HttpResponseBadRequest("Malformed data!")

        view.title = data['title']

        view.topology = data['topology']

        view.zoom = data['zoom']

        view.is_public = data['is_public']

        view.last_modified = datetime.datetime.now()
        fixed_nodes = data['nodes']

        view.display_orphans = data['display_orphans'] if data['display_orphans'] else False
        view.display_elinks = True if any(x == 'ELINK' for x in data['categories']) else False

        _update_map_categories(data['categories'], view)

        _update_map_node_positions(fixed_nodes, view)

        _LOGGER.debug('updating view metadata: %s' % view)

        view.save()

        return HttpResponse(view.viewid)
    else:
        return HttpResponseForbidden()

def create_map(request):
    session_user = get_account(request)

    try:
        data = simplejson.loads(request.raw_post_data)
    except KeyError:
        return HttpResponseBadRequest("Malformed data")

    # todo: sanitize input.
    view = NetmapView()
    view.title = data['title']
    view.owner = session_user
    #if 'link_tyes' in data:
    #    view.link_types = data['link_types']
    view.topology = data['topology']
    view.zoom = data['zoom']
    view.is_public = data['is_public']
    view.last_modified = datetime.datetime.now()
    fixed_nodes = data['nodes']
    view.display_orphans = data['display_orphans'] if data['display_orphans'] else False
    view.save()

    _update_map_categories(data['categories'], view)
    _update_map_node_positions(fixed_nodes, view)

    _LOGGER.debug('creating view metadata: %s' % view)

    return HttpResponse(view.viewid)


def get_map(request, map_id):
    view = get_object_or_404(NetmapView, pk=map_id)
    session_user = get_account(request)

    if view.is_public or (session_user == view.owner):
        json = view.to_json_dict()
        response = HttpResponse(simplejson.dumps(json))
        response['Content-Type'] = 'application/json; charset=utf-8'
        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
        response['x-nav-viewid'] = map_id
        return response
    else:
        return HttpResponseForbidden()

def maps(request):
    if request.method == 'POST':
        return create_map(request)
    elif request.method == 'GET':
        return get_maps(request)
    else:
        return HttpResponseBadRequest()

def get_maps(request):
    session_user = get_account(request)

    maps = NetmapView.objects.filter(
        Q(is_public=True) | Q(owner=session_user.id))\
    .order_by('-is_public')
    json_views =[]
    [json_views.append(view.to_json_dict()) for view in maps]
    return HttpResponse(simplejson.dumps(json_views))


def d3js_layer3(request, map_id=None):
    """
    Layer2 network topology representation in d3js force-direct graph layout
    http://mbostock.github.com/d3/ex/force.html
    """
    if map_id:
        view = get_object_or_404(NetmapView, pk=map_id)
        session_user = get_account(request)

        if view.is_public or (session_user == view.owner):
            json = _json_layer3(view)
            json['colormap']=traffic_gradient_map()
            response = HttpResponse(simplejson.dumps(json))
            response['Content-Type'] = 'application/json; charset=utf-8'
            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
            response['x-nav-viewid'] = map_id
            return response
        else:
            return HttpResponseForbidden()

    json = _json_layer3()
    json['colormap']=traffic_gradient_map()
    response = HttpResponse(simplejson.dumps(json))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response

def d3js_layer2(request, map_id=None):
    """
    Layer2 network topology representation in d3js force-direct graph layout
    http://mbostock.github.com/d3/ex/force.html
    """
    if map_id:
        view = get_object_or_404(NetmapView, pk=map_id)
        session_user = get_account(request)

        if view.is_public or (session_user == view.owner):
            json = _json_layer2(view)
            json['colormap']=traffic_gradient_map()
            response = HttpResponse(simplejson.dumps(json))
            response['Content-Type'] = 'application/json; charset=utf-8'
            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
            response['x-nav-viewid'] = map_id
            return response
        else:
            return HttpResponseForbidden()

    json = _json_layer2()
    json['colormap']=traffic_gradient_map()
    response = HttpResponse(simplejson.dumps(json))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response

def _json_layer2(view=None):
    graph = nx.Graph(build_netmap_layer2_graph(view))
    return d3_json_layer2(graph, None)

def _json_layer3(view=None):
    graph = nx.Graph(build_netmap_layer3_graph(view))
    return d3_json_layer3(graph, None)

def traffic_load_gradient(request):
    response = HttpResponse(simplejson.dumps(traffic_gradient_map()))
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


## not in use :
# ...

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
