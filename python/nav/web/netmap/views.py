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
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response

from django.template import RequestContext
from django.http import HttpResponse, HttpResponseForbidden,\
    HttpResponseBadRequest, HttpResponseRedirect
from django.utils import simplejson

import networkx as nx
from nav.django.utils import get_account, get_request_body
from nav.models.manage import Netbox, Category
from nav.models.profiles import NetmapView, NetmapViewNodePosition,\
    NetmapViewCategories, NetmapViewDefaultView, Account, AccountGroup
from nav.netmap.topology import build_netmap_layer3_graph,\
    build_netmap_layer2_graph
from nav.topology.d3_js.d3_js import d3_json_layer2, d3_json_layer3
from nav.web.netmap.common import traffic_gradient_map, layer2_graph
from nav.web.netmap.forms import NetmapDefaultViewForm

_LOGGER = logging.getLogger('nav.web.netmap')


def index(request):
    """Single page javascript app"""
    return backbone_app(request)


def backbone_app(request):
    session_user = get_account(request)

    link_to_admin = None
    if AccountGroup.ADMIN_GROUP in session_user.get_groups():
        link_to_admin = reverse('netmap-admin-views')

    response = render_to_response(
        'netmap/backbone.html',
        {
            'auth_id': session_user.id,
            'link_to_admin': link_to_admin,
            'navpath': [('Home', '/'), ('Netmap', '/netmap')]
        },
        RequestContext(request))

    return response


def admin_views(request):
    session_user = get_account(request)
    if session_user == Account.DEFAULT_ACCOUNT:
        return HttpResponseForbidden()

    global_favorite = None
    try:
        global_favorite = NetmapViewDefaultView.objects.get(
            owner=Account.DEFAULT_ACCOUNT)
    except ObjectDoesNotExist:
        pass # ignore it

    response = render_to_response(
        'netmap/admin_list_mapviews.html',
        {'views': NetmapView.objects.all(),
         'current_global_favorite': global_favorite,
         'navpath': [('Home', '/'), ('Netmap', '/netmap'),
                     ('Netmap Admin', '/netmap/admin')]
        },
        RequestContext(request))
    return response

# data views, d3js

def netmap(request, map_id):
    if request.method == 'PUT' or (
        'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META and
        request.META['HTTP_X_HTTP_METHOD_OVERRIDE'] == 'PUT'):
        return update_map(request, map_id)
    elif request.method == 'GET':
        return get_map(request, map_id)
    elif request.method == 'DELETE' or (
        'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META and
        request.META['HTTP_X_HTTP_METHOD_OVERRIDE'] == 'DELETE'):
        return delete_map(request, map_id)

    else:
        return HttpResponseBadRequest()


def netmap_defaultview(request):
    if request.method == 'PUT' or (
        'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META and
        request.META[
        'HTTP_X_HTTP_METHOD_OVERRIDE'] == 'PUT') or request.method == 'POST':
        map_id = None
        try:
            form = NetmapDefaultViewForm(request.POST)

            if form.is_valid():
                map_id = form.cleaned_data['map_id']

            if not map_id:
                data = simplejson.loads(get_request_body(request))
                map_id = data['viewid']
        except KeyError:
            return HttpResponseBadRequest("Malformed data! (1)")
        except ValueError:
            return HttpResponseBadRequest("Malformed data! (2)")
        if not map_id:
            return HttpResponseBadRequest("Malformed data! (3)")

        return update_defaultview(request, map_id)
    elif request.method == 'GET':
        return get_defaultview(request)
    else:
        return HttpResponseBadRequest()


def netmap_defaultview_global(request):
    if request.method == 'PUT' or (
        'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META and
        request.META[
        'HTTP_X_HTTP_METHOD_OVERRIDE'] == 'PUT') or request.method == 'POST':
        map_id = None
        try:
            form = NetmapDefaultViewForm(request.POST)

            if form.is_valid():
                map_id = form.cleaned_data['map_id']

            if not map_id:
                data = simplejson.loads(get_request_body(request))
                map_id = data['viewid']
        except KeyError:
            return HttpResponseBadRequest("Malformed data! (1)")
        except ValueError:
            return HttpResponseBadRequest("Malformed data! (2)")
        if not map_id:
            return HttpResponseBadRequest("Malformed data! (3)")

        # dirty anti ajax hack, since this is not using ajax yet.
        response = update_defaultview(request, map_id, True)
        if response.status_code == 200:
            return HttpResponseRedirect(reverse('netmap-admin-views'))
        else:
            return response

    elif request.method == 'GET':
        return get_global_defaultview(request)
    else:
        return HttpResponseBadRequest()


def update_defaultview(request, map_id, is_global_defaultview=False):
    """ Save/update a default view for a user.
    :param request: request
    :param map_id: NetmapView id
    :return: 200 HttpResponse with view_id or related http status code.
    """
    session_user = get_account(request)

    if session_user == Account.DEFAULT_ACCOUNT:
        return HttpResponseForbidden()

    view = get_object_or_404(NetmapView, pk=map_id)

    if is_global_defaultview:
        if AccountGroup.ADMIN_GROUP in session_user.get_groups():
            NetmapViewDefaultView.objects.filter(
                owner=Account(pk=Account.DEFAULT_ACCOUNT)).delete()
            default_view = NetmapViewDefaultView()
            default_view.view = view
            default_view.owner = Account(pk=Account.DEFAULT_ACCOUNT)
            default_view.save()
            return HttpResponse(default_view.view.viewid)
        else:
            return HttpResponseForbidden()
    else:
        if view.is_public or (session_user == view.owner):
            NetmapViewDefaultView.objects.filter(owner=session_user).delete()
            default_view = NetmapViewDefaultView()
            default_view.view = view
            default_view.owner = session_user
            default_view.save()
            return HttpResponse(default_view.view.viewid)
        else:
            return HttpResponseForbidden()


def get_global_defaultview(request):
    session_user = get_account(request)
    try:
        view = NetmapViewDefaultView.objects.get(owner=session_user)
    except ObjectDoesNotExist:
        view = get_object_or_404(NetmapViewDefaultView,
            owner=Account(pk=Account.DEFAULT_ACCOUNT))

    response = HttpResponse(simplejson.dumps(view.to_json_dict()))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response

def get_defaultview(request):
    session_user = get_account(request)

    view = get_object_or_404(NetmapViewDefaultView, owner=session_user)

    #permission?

    response = HttpResponse(simplejson.dumps(view.to_json_dict()))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response


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
    https://docs.djangoproject.com/en/dev/ref/models/querysets/#django.db
    .models.query.QuerySet.bulk_create
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
            data = simplejson.loads(get_request_body(request))
        except KeyError:
            return HttpResponseBadRequest("Malformed data!")

        view.title = data['title']

        view.description = data['description']

        view.topology = data['topology']

        view.zoom = data['zoom']

        view.is_public = data['is_public']

        view.last_modified = datetime.datetime.now()
        fixed_nodes = data['nodes']

        if data['display_orphans']:
            view.display_orphans = data['display_orphans']
        else:
            view.display_orphans = False

        if any(x == 'ELINK' for x in data['categories']):
            view.display_elinks = True
        else:
            view.display_elinks = False

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
        data = simplejson.loads(get_request_body(request))
    except KeyError:
        return HttpResponseBadRequest("Malformed data")

    # todo: sanitize input.
    view = NetmapView()
    view.title = data['title']
    view.description = data['description']
    view.owner = session_user
    #if 'link_tyes' in data:
    #    view.link_types = data['link_types']
    view.topology = data['topology']
    view.zoom = data['zoom']
    view.is_public = data['is_public']
    view.last_modified = datetime.datetime.now()
    fixed_nodes = data['nodes']
    if data['display_orphans']:
        view.display_orphans = data['display_orphans']
    else:
        view.display_orphans = False
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

def delete_map(request, map_id):
    view = get_object_or_404(NetmapView, pk=map_id)
    session_user = get_account(request)

    if session_user == view.owner or AccountGroup.ADMIN_GROUP in session_user.get_groups():
        view.delete()
        return HttpResponse()
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

    _maps = NetmapView.objects.filter(
        Q(is_public=True) | Q(owner=session_user.id))\
    .order_by('-is_public')
    json_views = []
    [json_views.append(view.to_json_dict()) for view in _maps]
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
    traffic = traffic_gradient_map()
    keys = ('r','g','b')

    # again thar be dragons.
    response = HttpResponse(
        simplejson.dumps(([dict(zip(keys, traffic)) for traffic in traffic])))
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


## not in use :
# ...

# data views, graphml
def graphml_layer2(request):
    """Layer2 network topology representation in graphml format."""

    netboxes, connections = layer2_graph()

    response = render_to_response(
        'netmap/graphml.html',
        {'netboxes': netboxes,
         'connections': connections,
         'layer': 2,
         'navpath': [('Home', '/'), ('Netmap', '/netmap')]
        },
        RequestContext(request)
    )
    response['Content-Type'] = 'application/xml; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response
