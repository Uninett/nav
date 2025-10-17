#
# Copyright (C) 2007, 2010, 2011, 2014 Uninett AS
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
"""Netmap views"""

import json

from django.db.models import Q
from django.views.generic import TemplateView, ListView

from nav.web.auth.utils import get_account
from nav.models.profiles import (
    NetmapView,
    NetmapViewDefaultView,
    Account,
)
from nav.models.manage import Category, Room, Location

from .mixins import DefaultNetmapViewMixin, AdminRequiredMixin
from .serializers import NetmapViewSerializer
from .graph import get_traffic_gradient


class IndexView(DefaultNetmapViewMixin, TemplateView):
    """Main view for Netmap"""

    template_name = 'netmap/netmap.html'

    def get_context_data(self, **kwargs):
        user = get_account(self.request)

        context = super(IndexView, self).get_context_data(user=user, **kwargs)

        netmap_views = NetmapView.objects.all()
        if not user.is_admin():
            netmap_views = netmap_views.filter(
                Q(is_public=True) | Q(owner=user)
            ).select_related(
                'owner',
            )

        netmap_views_json = json.dumps(
            NetmapViewSerializer(netmap_views, many=True).data
        )

        categories = list(Category.objects.values_list('id', flat=True))
        categories.append('ELINK')

        rooms_locations = json.dumps(
            list(Room.objects.values_list('id', flat=True))
            + list(Location.objects.values_list('id', flat=True))
        )

        context.update(
            {
                'account': user,
                'netmap_views': netmap_views,
                'netmap_views_json': netmap_views_json,
                'categories': categories,
                'rooms_locations': rooms_locations,
                'traffic_gradient': get_traffic_gradient(),
                'navpath': [('Home', '/'), ('Netmap',)],
            }
        )

        return context


class NetmapAdminView(AdminRequiredMixin, ListView):
    """View for Netmap admin functions"""

    context_object_name = 'views'
    model = NetmapView
    template_name = 'netmap/admin.html'

    def get_context_data(self, **kwargs):
        context = super(NetmapAdminView, self).get_context_data(**kwargs)

        try:
            global_default_view = NetmapViewDefaultView.objects.select_related(
                'view'
            ).get(owner=Account.DEFAULT_ACCOUNT)
        except NetmapViewDefaultView.DoesNotExist:
            global_default_view = None

        context.update(
            {
                'navpath': [('Home', '/'), ('Netmap', '/netmap/'), ('Netmap admin',)],
                'global_default_view': global_default_view,
            }
        )

        return context
