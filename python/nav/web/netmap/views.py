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
"""Netmap views"""
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import BaseUpdateView
from django.utils import simplejson

from rest_framework import viewsets, filters, status
from rest_framework import generics
from rest_framework.response import Response

from nav.django.utils import get_account
from nav.models.profiles import (
    NetmapView,
    NetmapViewCategories,
    NetmapViewDefaultView,
    NetmapViewNodePosition,
    Account,
)
from nav.models.manage import Category

from .mixins import DefaultNetmapViewMixin, AdminRequiredMixin
from .serializers import NetmapViewSerializer, NetmapViewDefaultViewSerializer


class IndexView(DefaultNetmapViewMixin, TemplateView):
    template_name = 'netmap/netmap.html'

    def get_context_data(self, **kwargs):

        self.account = get_account(self.request)

        context = super(IndexView, self).get_context_data(**kwargs)

        netmap_views = NetmapView.objects.filter(
            Q(is_public=True) | Q(owner=self.account)
        )

        categories = list(Category.objects.all())
        categories.append(Category(id='ELINK', description='ELINK'))

        context.update({
            'account': self.account,
            'netmap_views': netmap_views,
            'categories': categories,
            'navpath': [('Home', '/'), ('Netmap', '/netmap')]
        })

        return context


class NetmapAdminView(AdminRequiredMixin, ListView):
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
                ('Netmap', '/netmap'),
                ('Netmap admin', 'netmap/admin')
            ],
            'global_default_view': global_default_view
        })

        return context


class NetmapViewList(generics.ListAPIView):

    serializer_class = NetmapViewSerializer

    def get_queryset(self):
        user = get_account(self.request)
        return NetmapView.objects.filter(
            Q(is_public=True) | Q(owner=user)
        )


class NetmapViewCreate(generics.CreateAPIView):

    serializer_class = NetmapViewSerializer

    def pre_save(self, obj):
        user = get_account(self.request)
        obj.owner = user

    def post_save(self, obj, created=False):
        if created:
            for category in obj.categories:
                # Since a new NetmapView object is always created
                # there is no need for further checks.
                # FIXME: User bulk_create?
                NetmapViewCategories.objects.create(
                    view=obj,
                    category=Category.objects.get(id=category)
                )


class NetmapViewEdit(generics.RetrieveUpdateDestroyAPIView):

    lookup_field = 'viewid'
    serializer_class = NetmapViewSerializer

    def get_queryset(self):
        user = get_account(self.request)
        return NetmapView.objects.filter(
            Q(is_public=True) | Q(owner=user)
        )

    # TODO: Override post_(save/delete)

    def get_object_or_none(self):
        try:
            return self.get_object()
        except Http404:
            # Models should not be created in this view.
            # Overridden to raise exception on PUT requests
            # as well as on PATCH
            raise


class NetmapViewDefaultViewUpdate(generics.RetrieveUpdateAPIView):

    lookup_field = 'owner'
    queryset = NetmapViewDefaultView.objects.all()
    serializer_class = NetmapViewDefaultViewSerializer

    def pre_save(self, obj):
        # For some reason beyond my understanding, using a lookup_field
        # that is a foreign key relation causes the parent implementation
        # of this method to raise an exception.
        pass

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


### Test view

class NetmapTestView(TemplateView):
    template_name = 'netmap/test_graph.html'