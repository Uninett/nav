#
# Copyright (C) 2007, 2010, 2011, 2014 Uninett AS
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
"""Netmap views"""
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404
from django.views.generic import TemplateView, ListView
from django.shortcuts import get_object_or_404

from rest_framework import status, generics, views
from rest_framework.response import Response
from rest_framework.renderers import UnicodeJSONRenderer as JSONRenderer

from nav.django.utils import get_account
from nav.models.profiles import (
    NetmapView,
    NetmapViewCategories,
    NetmapViewDefaultView,
    NetmapViewNodePosition,
    Account,
)
from nav.models.manage import Category, Netbox, Room, Location

from .mixins import DefaultNetmapViewMixin, AdminRequiredMixin
from .serializers import (
    NetmapViewSerializer,
    NetmapViewDefaultViewSerializer,
)
from .graph import (
    get_topology_graph,
    get_traffic_gradient,
    get_layer2_traffic,
    get_layer3_traffic,
)
from .cache import update_cached_node_positions, cache_exists

# Ignore linting errors from DRF class hierarchy
# pylint: disable=R0901,R0904


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

        netmap_views_json = JSONRenderer().render(
            NetmapViewSerializer(netmap_views, many=True).data
        )

        categories = list(Category.objects.values_list('id', flat=True))
        categories.append('ELINK')

        rooms_locations = JSONRenderer().render(
            list(Room.objects.values_list('id', flat=True)) +
            list(Location.objects.values_list('id', flat=True))
        )

        context.update({
            'account': user,
            'netmap_views': netmap_views,
            'netmap_views_json': netmap_views_json,
            'categories': categories,
            'rooms_locations': rooms_locations,
            'traffic_gradient': get_traffic_gradient(),
            'navpath': [('Home', '/'), ('Netmap',)]
        })

        return context


class TrafficView(views.APIView):
    """Fetches traffic data for the links and returns it in JSON format"""

    renderer_classes = (JSONRenderer,)

    # TODO: add location filter
    def get(self, _request, *args, **kwargs):
        """Controller for GET-requests for Traffic data"""
        layer = int(kwargs.pop('layer', 2))
        # TODO: should probably use id
        roomid = kwargs.pop('roomid')
        try:
            if layer == 3:
                traffic = get_layer3_traffic(roomid)
            else:
                traffic = get_layer2_traffic(roomid)
        except ObjectDoesNotExist:
            raise Http404()
        return Response(traffic)


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
            ).get(
                owner=Account.DEFAULT_ACCOUNT
            )
        except NetmapViewDefaultView.DoesNotExist:
            global_default_view = None

        context.update({
            'navpath': [
                ('Home', '/'),
                ('Netmap', '/netmap/'),
                ('Netmap admin',)
            ],
            'global_default_view': global_default_view
        })

        return context


class NetmapViewList(generics.ListAPIView):
    """
    View for returning a list of NetmapViews which are public or
    belonging to the current account
    """
    serializer_class = NetmapViewSerializer

    def get_queryset(self):
        user = get_account(self.request)
        return NetmapView.objects.filter(
            Q(is_public=True) | Q(owner=user)
        )


class NetmapViewCreate(generics.CreateAPIView):
    """View for creating a NetmapView"""
    serializer_class = NetmapViewSerializer

    def pre_save(self, obj):
        user = get_account(self.request)
        obj.owner = user

    def post_save(self, obj, created=False):
        if created:
            NetmapViewCategories.objects.bulk_create([
                NetmapViewCategories(
                    view=obj,
                    category=Category.objects.get(id=category)
                )
                for category in obj.categories
            ])


class NetmapViewEdit(generics.RetrieveUpdateDestroyAPIView):
    """View for saving a NetmapView"""
    lookup_field = 'viewid'
    serializer_class = NetmapViewSerializer

    def get_queryset(self):
        user = get_account(self.request)
        if user.is_admin():
            return NetmapView.objects.all()
        else:
            return NetmapView.objects.filter(owner=user)

    def post_save(self, obj, created=False):
        old_categories = set(
            obj.categories_set.values_list('category', flat=True))
        new_categories = set(obj.categories)
        to_delete = old_categories - new_categories
        to_save = new_categories - old_categories

        # Delete removed categories
        obj.categories_set.filter(category__in=to_delete).delete()

        # Create added categories
        NetmapViewCategories.objects.bulk_create([
            NetmapViewCategories(view=obj, category=Category(id=category))
            for category in to_save
        ])

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            # Models should not be created in this view.
            # Overridden to raise exception on PUT requests
            # as well as on PATCH
            raise


class NetmapViewDefaultViewUpdate(generics.RetrieveUpdateAPIView):
    """View for setting the default NetmapView of an account"""
    lookup_field = 'owner'
    queryset = NetmapViewDefaultView.objects.all()
    serializer_class = NetmapViewDefaultViewSerializer

    def pre_save(self, obj):
        # For some reason beyond my understanding, using a lookup_field
        # that is a foreign key relation causes the parent implementation
        # of this method to raise an exception.
        pass

    def post_save(self, obj, created=False):
        # If a non-public view was set to be the global default, change
        # that view's visibility to public.
        if obj.owner.id is Account.DEFAULT_ACCOUNT and not obj.view.is_public:
            obj.view.is_public = True
            obj.view.save()

    def update(self, request, *args, **kwargs):

        if not self._is_owner_or_admin():
            return Response(status.HTTP_401_UNAUTHORIZED)

        return super(NetmapViewDefaultViewUpdate, self).update(
            request,
            args,
            kwargs,
        )

    def retrieve(self, request, *args, **kwargs):

        if not self._is_owner_or_admin():
            return Response(status.HTTP_401_UNAUTHORIZED)

        return super(NetmapViewDefaultViewUpdate, self).retrieve(
            request,
            args,
            kwargs,
        )

    def _is_owner_or_admin(self):

        user = get_account(self.request)
        ownerid = self.kwargs.get(self.lookup_field, Account.DEFAULT_ACCOUNT)

        return user.id == ownerid or user.is_admin()


class NodePositionUpdate(generics.UpdateAPIView):
    """View for updating node positions"""
    def update(self, request, *args, **kwargs):

        viewid = kwargs.pop('viewid')
        data = request.DATA.get('data', [])
        # nodes to be updated in the topology cache
        cache_updates = []
        for d in data:
            defaults = {
                'x': int(d['x']),
                'y': int(d['y']),
            }
            obj, created = NetmapViewNodePosition.objects.get_or_create(
                viewid=NetmapView(pk=viewid),
                netbox=Netbox(pk=int(d['netbox'])),
                defaults=defaults
            )
            if not created:
                obj.x = defaults['x']
                obj.y = defaults['y']
                obj.save()
            cache_updates.append({
                "id": str(obj.netbox.id),
                "x": defaults["x"],
                "y": defaults["y"],
                "new_node": created
            })
        # Invalidate cached position
        if cache_exists("topology", viewid, "layer 2"):
            update_cached_node_positions(viewid, "layer 2", cache_updates)
        if cache_exists("topology", viewid, "layer 3"):
            update_cached_node_positions(viewid, "layer 3", cache_updates)
        return Response({"status": "OK"})


class NetmapGraph(views.APIView):
    """View for building and providing topology data in graph form"""
    def get(self, request, **kwargs):

        load_traffic = 'traffic' in request.GET
        layer = int(kwargs.get('layer', 2))
        viewid = kwargs.get('viewid')
        view = None

        if viewid is not None:
            view = get_object_or_404(NetmapView, pk=viewid)

        return Response(get_topology_graph(layer, load_traffic, view))
