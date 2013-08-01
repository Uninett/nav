#
# Copyright (C) 2007-2008 UNINETT AS
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
"""Network Explorer view functions"""
from django.views.generic import TemplateView
from django.views.generic import View
from django.views.generic.list import BaseListView
from django.views.generic.detail import BaseDetailView

from nav.models.manage import Netbox
from nav.models.manage import Interface
from search import vlan_search, portname_search, search

from .forms import NetworkSearchForm
from .mixins import (
    GetRoutersMixin,
    JSONResponseMixin,
    ExpandRouterContextMixin,
    ExpandGWPortMixin,
    ExpandSwitchContextMixin,
    ExpandSWPortContextMixin)


PATH = [("Home", "/"), ("Network Explorer", "/networkexplorer/")]


class IndexView(TemplateView):
    """Basic view of the network"""
    template_name = 'networkexplorer/base.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context.update({'path': PATH, 'form': NetworkSearchForm()})
        return context


class RouterJSONView(JSONResponseMixin, GetRoutersMixin, BaseListView):
    """Returns a JSON-response of the routers on the network"""

    def render_to_response(self, context):
        return self.render_json_response(context)


class ExpandRouterView(
        JSONResponseMixin, ExpandRouterContextMixin, BaseDetailView):
    """Returns a JSON-response of a router's gwports"""
    model = Netbox

    def render_to_response(self, context):
        return self.render_json_response(context)


class ExpandGWPortView(
        JSONResponseMixin, ExpandGWPortMixin, BaseDetailView):
    """Returns a JSON-response of a gwport's swports and switches"""
    model = Interface

    def render_to_response(self, context):
        return self.render_json_response(context)


class ExpandSwitchView(
        JSONResponseMixin, ExpandSwitchContextMixin, BaseDetailView):
    """Returns a JSON-response of a switch's swport-vlans"""
    model = Netbox

    def render_to_response(self, context):
        return self.render_json_response(context)


class ExpandSWPortView(
        JSONResponseMixin, ExpandSWPortContextMixin, BaseDetailView):
    """Returns a JSON-response of a swport's services and active hosts"""
    model = Interface

    def render_to_response(self, context):
        return self.render_json_response(context)


class SearchView(JSONResponseMixin, View):
    json_dumps_kwargs = {'indent': 2}

    # TODO: Monday work on this!!!!

    def form_invalid(self, form):
        return {'error': form.errors}

    def form_valid(self, form):
        return search(form.cleaned_data)

    def get(self, request, *args, **kwargs):
        form = NetworkSearchForm(request.GET)

        if form.is_valid():
            context = self.form_valid(form)
        else:
            context = self.form_invalid(form)

        return self.render_json_response(context)


# def search(request):
#     """
#     """
#     # Raise 404 if no parameters are given
#     if 'lookup_field' not in request.GET:
#         raise Http404
#
#     router_matches = []
#     gwport_matches = []
#     swport_matches = []
#
#     if request.REQUEST.get('exact', None) == 'on':
#         exact = True
#     else:
#         exact = False
#
#     if request.GET['lookup_field'] == 'sysname':
#         result = sysname_search(request.GET['query'], exact)
#         router_matches = result[0]
#         gwport_matches = result[1]
#         swport_matches = result[2]
#
#     if request.GET['lookup_field'] == 'ip':
#         result = ip_search(request.GET['query'], exact)
#         router_matches = result[0]
#         gwport_matches = result[1]
#         swport_matches = result[2]
#
#     if request.GET['lookup_field'] == 'mac':
#         result = mac_search(unquote(request.GET['query']))
#         router_matches = result[0]
#         gwport_matches = result[1]
#         swport_matches = result[2]
#
#     if request.GET['lookup_field'] == 'room':
#         result = room_search(request.GET['query'], exact)
#         router_matches = result[0]
#         gwport_matches = result[1]
#         swport_matches = result[2]
#
#     if request.GET['lookup_field'] == 'vlan':
#         result = vlan_search(request.GET['query'], exact)
#         router_matches = result[0]
#         gwport_matches = result[1]
#         swport_matches = result[2]
#
#     if request.GET['lookup_field'] == 'port':
#         result = portname_search(request.GET['query'], exact)
#         router_matches = result[0]
#         gwport_matches = result[1]
#         swport_matches = result[2]
#
#
#     # A bit ugly hack to remove duplicates, but simplejson doesnt seem to support sets
#     router_matches = list(set(router_matches))
#     gwport_matches = list(set(gwport_matches))
#     swport_matches = list(set(swport_matches))
#
#     if request.REQUEST.get('hide', False):
#         for gwport in gwport_matches:
#             if not gwport.ifalias:
#                 gwport_matches.remove(gwport)
#         for swport in swport_matches:
#             if not swport.ifalias:
#                 swport_matches.remove(swport)
#
#     # Get the html up-front
#     routers = []
#     for router in router_matches:
#         req = HttpRequest()
#         req.GET['netboxid'] = router.id
#         routers.append([router.id, expand_router(req).content])
#
#     gwports = []
#     for gwport in gwport_matches:
#         req = HttpRequest()
#         req.GET['gwportid'] = gwport.id
#         gwports.append([gwport.id, expand_gwport(req).content])
#
#     swports = []
#     for swport in swport_matches:
#         req = HttpRequest()
#         req.GET['swportid'] = swport.id
#         swports.append([swport.id, expand_swport(req).content])
#
#     return HttpResponse(json.dumps({'routers': routers, 'gwports': gwports, 'swports': swports}))
