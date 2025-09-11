#
# Copyright (C) 2007-2008 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
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

from .search import search
from .forms import NetworkSearchForm
from .mixins import (
    GetRoutersMixin,
    JSONResponseMixin,
    ExpandRouterContextMixin,
    ExpandGWPortMixin,
    ExpandSwitchContextMixin,
    ExpandSWPortContextMixin,
)


PATH = [("Home", "/"), ("Network Explorer", "/networkexplorer/")]


class IndexView(TemplateView):
    """Basic view of the network"""

    template_name = 'networkexplorer/base.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context.update({'navpath': PATH, 'form': NetworkSearchForm()})
        return context


class RouterJSONView(JSONResponseMixin, GetRoutersMixin, BaseListView):
    """Returns a JSON-response of the routers on the network"""

    def render_to_response(self, context):
        return self.render_json_response(context)


class ExpandRouterView(JSONResponseMixin, ExpandRouterContextMixin, BaseDetailView):
    """Returns a JSON-response of a router's gwports"""

    model = Netbox

    def render_to_response(self, context):
        return self.render_json_response(context)


class ExpandGWPortView(JSONResponseMixin, ExpandGWPortMixin, BaseDetailView):
    """Returns a JSON-response of a gwport's swports and switches"""

    model = Interface

    def render_to_response(self, context):
        return self.render_json_response(context)


class ExpandSwitchView(JSONResponseMixin, ExpandSwitchContextMixin, BaseDetailView):
    """Returns a JSON-response of a switch's swport-vlans"""

    model = Netbox

    def render_to_response(self, context):
        return self.render_json_response(context)


class ExpandSWPortView(JSONResponseMixin, ExpandSWPortContextMixin, BaseDetailView):
    """Returns a JSON-response of a swport's services and active hosts"""

    model = Interface

    def render_to_response(self, context):
        return self.render_json_response(context)


class SearchView(JSONResponseMixin, View):
    def form_invalid(self, form):
        return {'errors': form.errors}

    def form_valid(self, form):
        return search(form.cleaned_data)

    def get(self, request, *_args, **_kwargs):
        form = NetworkSearchForm(request.GET)
        status = 200

        if form.is_valid():
            context = self.form_valid(form)
        else:
            context = self.form_invalid(form)
            status = 400

        return self.render_json_response(context, status=status)
