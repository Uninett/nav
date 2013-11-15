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
"""Netmap view functions for Django"""
import datetime
import logging
import os
from django.conf import settings
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response

from django.template import RequestContext
from django.http import (HttpResponse, HttpResponseForbidden,
                         HttpResponseBadRequest, HttpResponseRedirect)
from django.utils import simplejson

import nav.buildconf
from nav.django.utils import get_account, get_request_body
from nav.models.manage import Netbox, Category
from nav.models.profiles import (NetmapView, NetmapViewNodePosition,
                                 NetmapViewCategories, NetmapViewDefaultView,
                                 Account)
from nav.netmap.metadata import (node_to_json_layer2, edge_to_json_layer2,
                                 node_to_json_layer3, edge_to_json_layer3,
                                 vlan_to_json, get_vlan_lookup_json)

from nav.netmap.topology import (build_netmap_layer3_graph,
                                 build_netmap_layer2_graph,
                                 _get_vlans_map_layer2, _get_vlans_map_layer3)
from nav.topology import vlan
from nav.web.netmap.common import layer2_graph, get_traffic_rgb
from nav.web.netmap.forms import NetmapDefaultViewForm

_LOGGER = logging.getLogger('nav.web.netmap')


def _get_available_categories():
    """Return a list of categories in NAV, and adding the fictive
     ELINK category
     """
    available_categories = list(Category.objects.all())
    available_categories.append(Category(id='ELINK', description='ELINK'))
    return available_categories

def backbone_app(request):
    """Single page backbone application for Netmap"""
    session_user = get_account(request)

    link_to_admin = None
    if session_user.is_admin():
        link_to_admin = reverse('netmap-admin-views')

    available_categories = _get_available_categories()

    response = render_to_response(
        'netmap/backbone.html',
        {
            'bootstrap_mapproperties_collection': _get_maps(request),
            'bootstrap_isFavorite': _get_global_defaultview_as_json(request),
            'bootstrap_availableCategories': serializers.serialize(
                'json',
                available_categories,
                fields=('description')
            ),
            'bootstrap_availableCategories_datauris': simplejson.dumps(
                _get_datauris_for_categories()
            ),
            'auth_id': session_user.id,
            'link_to_admin': link_to_admin,
            'navpath': [('Home', '/'), ('Netmap', '/netmap')]
        },
        RequestContext(request))
    return response


def admin_views(request):
    """Admin page

    User can set default netmap view for all users in here
    """
    session_user = get_account(request)
    if not session_user.is_admin():
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
    """Wrapper request view for fetching a nav.models.Map in JS-app

    It call the helper request methods for update, get and delete
    :throws HttpResponseBadRequest if wrapper cannot manage request
    """
    if request.method == 'PUT' or (
        'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META and
        request.META['HTTP_X_HTTP_METHOD_OVERRIDE'] == 'PUT'):
        return _update_map(request, map_id)
    elif request.method == 'GET':
        return _get_map(request, map_id)
    elif request.method == 'DELETE' or (
        'HTTP_X_HTTP_METHOD_OVERRIDE' in request.META and
        request.META['HTTP_X_HTTP_METHOD_OVERRIDE'] == 'DELETE'):
        return _delete_map(request, map_id)

    else:
        return HttpResponseBadRequest()


def netmap_defaultview(request):
    """Wrapper request view for users default view (nav.models.Map in JS-app)

    It call the helper request methods for update and get.
    :throws HttpResponseBadRequest if wrapper cannot manage request
    """
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
        response = HttpResponse(_get_defaultview(request))
        response['Content-Type'] = 'application/json; charset=utf-8'
        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
        return response
    else:
        return HttpResponseBadRequest()


def netmap_defaultview_global(request):
    """Wrapper request view for global default view (nav.models.Map in JS-app)

    It call the helper request methods for update, get and delete
    :throws HttpResponseBadRequest if wrapper cannot manage request
    """
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
        response = HttpResponse(_get_global_defaultview_as_json(request))
        response['Content-Type'] = 'application/json; charset=utf-8'
        response['Cache-Control'] = 'no-cache'
        response['Pragma'] = 'no-cache'
        response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
        return response
    else:
        return HttpResponseBadRequest()

@transaction.commit_on_success
def update_defaultview(request, map_id, is_global_defaultview=False):
    """ Save/update a default view for a user.
    :param request: request
    :param map_id: NetmapView id
    :return: 200 HttpResponse with view_id or related http status code.
    """
    session_user = get_account(request)

    if not session_user.is_admin():
        return HttpResponseForbidden()

    view = get_object_or_404(NetmapView, pk=map_id)

    if is_global_defaultview:
        if session_user.is_admin():
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


def _get_global_defaultview_as_json(request):
    """Helper for fetching global default view"""
    session_user = get_account(request)
    try:
        view = NetmapViewDefaultView.objects.get(owner=session_user)
    except ObjectDoesNotExist:
        try:
            view = NetmapViewDefaultView.objects.get(
                owner=Account(pk=Account.DEFAULT_ACCOUNT))
        except ObjectDoesNotExist:
            view = None

    return simplejson.dumps(view.to_json_dict()) if view else 'null'

def _get_defaultview(request):
    """Helper for fetching users default view"""
    session_user = get_account(request)

    view = get_object_or_404(NetmapViewDefaultView, owner=session_user)

    #permission?
    return simplejson.dumps(view.to_json_dict())


def _update_map_node_positions(fixed_nodes, view):
    """Helper for updating node positions for a given netmap view

    :param fixed_nodes: List of node objects to fetch it's fixed positions from
    :param view: Which view to update.
    :type fixed_nodes: list of json node objects.
    :type view: NetmapView
    """
    NetmapViewNodePosition.objects.filter(viewid=view.pk).delete()
    for node in fixed_nodes:
        netbox = Netbox.objects.get(pk=node['id'])

        NetmapViewNodePosition.objects.create(
            viewid=view,
            netbox=netbox,
            x=node['position']['x'],
            y=node['position']['y'])


def _update_map_categories(categories, view):
    """ todo django 1.4
    https://docs.djangoproject.com/en/dev/ref/models/querysets/#django.db
    .models.query.QuerySet.bulk_create
    https://docs.djangoproject.com/en/dev/releases/1.4/
    https://code.djangoproject.com/ticket/7596
    """
    NetmapViewCategories.objects.filter(view=view.pk).delete()
    for category in categories:
        if category['name'] != 'ELINK' and category['is_selected']:
            category_model = Category.objects.get(pk=category['name'])

            NetmapViewCategories.objects.create(
                view=view,
                category=category_model)

@transaction.commit_on_success
def _update_map(request, map_id):
    """Helper for updating/saving a netmap view

    :param request: Request from wrapper
    :param map_id: Map id to update/save
    """
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

        if any(x['name'] == 'ELINK' for x in data['categories']):
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

@transaction.commit_on_success
def _create_map(request):
    """Helper method for creating a new netmap view

    :param request: request from wrapper method.
    """
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


def _get_map(request, map_id):
    """Helper method for fetching a saved netmap view as json

    :param request: Request from wrapper function
    :param map_id: map_id to fetch.
    """
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

@transaction.commit_on_success
def _delete_map(request, map_id):
    """Helper method for deleting a netmap view

    :param request: Request from wrapper function
    :param map_id: Map id to delete.
    """
    view = get_object_or_404(NetmapView, pk=map_id)
    session_user = get_account(request)

    if session_user == view.owner or session_user.is_admin():
        view.delete()
        return HttpResponse()
    else:
        return HttpResponseForbidden()



def maps(request):
    """ Wrapper function fetching/updating netmap views"""
    if request.method == 'POST':
        return _create_map(request)
    elif request.method == 'GET':
        return HttpResponse(_get_maps(request))
    else:
        return HttpResponseBadRequest()


def _get_maps(request):
    """Helper method for fetching netmap views

    :param request: Request from wrapper function
    """
    session_user = get_account(request)
    netmap_views = NetmapView.objects.filter(
        Q(is_public=True) | Q(owner=session_user.id)
    ).order_by('-is_public')
    json_views = [view.to_json_dict() for view in netmap_views]
    return simplejson.dumps(json_views)


def api_graph_layer_3(request, map_id=None):
    """
    Layer2 network topology representation in d3js force-direct graph layout
    http://mbostock.github.com/d3/ex/force.html
    """
    load_traffic = 'traffic' in request.GET

    if map_id:
        view = get_object_or_404(NetmapView, pk=map_id)
        session_user = get_account(request)

        if view.is_public or (session_user == view.owner):
            json = _json_layer3(load_traffic, view)
            response = HttpResponse(simplejson.dumps(json))
            response['Content-Type'] = 'application/json; charset=utf-8'
            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
            response['x-nav-viewid'] = map_id
            return response
        else:
            return HttpResponseForbidden()

    json = _json_layer3(load_traffic)
    response = HttpResponse(simplejson.dumps(json))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response


def api_graph_layer_2(request, map_id=None):
    """
    Layer2 network topology representation in d3js force-direct graph layout
    http://mbostock.github.com/d3/ex/force.html
    """
    load_traffic = 'traffic' in request.GET

    if map_id:
        view = get_object_or_404(NetmapView, pk=map_id)
        session_user = get_account(request)

        if view.is_public or (session_user == view.owner):
            json = _json_layer2(load_traffic, view)
            response = HttpResponse(simplejson.dumps(json))
            response['Content-Type'] = 'application/json; charset=utf-8'
            response['Cache-Control'] = 'no-cache'
            response['Pragma'] = 'no-cache'
            response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
            response['x-nav-viewid'] = map_id
            return response
        else:
            return HttpResponseForbidden()

    json = _json_layer2(load_traffic)
    response = HttpResponse(simplejson.dumps(json))
    response['Content-Type'] = 'application/json; charset=utf-8'
    response['Cache-Control'] = 'no-cache'
    response['Pragma'] = 'no-cache'
    response['Expires'] = "Thu, 01 Jan 1970 00:00:00 GMT"
    return response


def _json_layer2(load_traffic=False, view=None):
    _LOGGER.debug("build_netmap_layer2_graph() start")
    topology_without_metadata = vlan.build_layer2_graph(
        (
        'to_interface__netbox', 'to_interface__netbox__room', 'to_netbox__room',
        'netbox__room', 'to_interface__netbox__room__location',
        'to_netbox__room__location', 'netbox__room__location'))
    _LOGGER.debug("build_netmap_layer2_graph() topology graph done")

    vlan_by_interface, vlan_by_netbox = _get_vlans_map_layer2(
        topology_without_metadata)
    _LOGGER.debug("build_netmap_layer2_graph() vlan mappings done")

    graph = build_netmap_layer2_graph(topology_without_metadata,
                                      vlan_by_interface, vlan_by_netbox,
                                      load_traffic, view)

    return {
        'vlans': get_vlan_lookup_json(vlan_by_interface),
        'nodes': _get_nodes(node_to_json_layer2, graph),
        'links': [edge_to_json_layer2((node_a, node_b), nx_metadata) for
                  node_a, node_b, nx_metadata in graph.edges_iter(data=True)]
    }


def _json_layer3(load_traffic=False, view=None):
    _LOGGER.debug("build_netmap_layer3_graph() start")
    topology_without_metadata = vlan.build_layer3_graph(
        ('prefix__vlan__net_type', 'gwportprefix__prefix__vlan__net_type',))
    _LOGGER.debug("build_netmap_layer3_graph() topology graph done")

    vlans_map = _get_vlans_map_layer3(topology_without_metadata)
    _LOGGER.debug("build_netmap_layer2_graph() vlan mappings done")

    graph = build_netmap_layer3_graph(topology_without_metadata, load_traffic,
                                      view)
    return {
        'vlans': [vlan_to_json(prefix.vlan) for prefix in vlans_map],
        'nodes': _get_nodes(node_to_json_layer3, graph),
        'links': [edge_to_json_layer3((node_a, node_b), nx_metadata) for
                  node_a, node_b, nx_metadata in graph.edges_iter(data=True)]
    }

def _get_nodes(node_to_json_function, graph):
    nodes = {}
    for node, nx_metadata in graph.nodes_iter(data=True):
        nodes.update(node_to_json_function(node, nx_metadata))
    return nodes



def traffic_load_gradient(request):
    """Json with 100 items where each row represent the RGB color load
    indexed by percentage."""
    keys = ('r', 'g', 'b')

    # again thar be dragons.
    response = HttpResponse(
        simplejson.dumps((
        [dict(zip(keys, get_traffic_rgb(percent))) for percent in
         range(0, 101)])))
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


def _convert_image_to_datauri(catid):
    """Helper function for converting one image to base64 inline css"""
    static_dir = settings.STATICFILES_DIRS[0]
    image_base = os.path.join(
        nav.buildconf.webrootdir, static_dir, "images", "netmap")
    filename = "{0}.png".format(catid.lower())

    for image in (filename, "other.png"):
        filepath = os.path.join(image_base, image)
        try:
            with open(filepath, "rb") as data:
                return data.read().encode("base64").replace("\n", "")
        except IOError:
            pass


def _get_datauris_for_categories():
    """Helper function for fetching datauris for every category"""
    data_uris = {}

    for category in _get_available_categories():
        data_uris[category.id.lower()] = _convert_image_to_datauri(category.id)
    return data_uris

def api_datauris_categories(request):
    """Converts node categories images to inline base64 datauri images

    :param request: Request
    """

    response = HttpResponse(
        simplejson.dumps(_get_datauris_for_categories())
    )
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
