#
# Copyright (C) 2013 Uninett AS
# Copyright (C) 2022 Sikt
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
"""Urlconf for the NAV REST api"""

from django.urls import re_path, include, path
from rest_framework import routers

from nav.auditlog import api as auditlogapi
from nav.web.api.v1 import views

router = routers.SimpleRouter()
router.register(r'account', views.AccountViewSet)
router.register(r'accountgroup', views.AccountGroupViewSet, basename='accountgroup')
router.register(r'rack', views.RackViewSet)
router.register(r'room', views.RoomViewSet)
router.register(r'location', views.LocationViewSet)
router.register(
    r'management-profile',
    views.ManagementProfileViewSet,
    basename="management-profile",
)
router.register(r'netbox', views.NetboxViewSet)
router.register(r'interface', views.InterfaceViewSet)
router.register(r'prefix', views.PrefixViewSet)
router.register(r'vlan', views.VlanViewSet)
router.register(r'cabling', views.CablingViewSet, basename='cabling')
router.register(r'patch', views.PatchViewSet, basename='patch')
router.register(r'cam', views.CamViewSet, basename='cam')
router.register(r'arp', views.ArpViewSet, basename='arp')
router.register(
    r'servicehandler', views.ServiceHandlerViewSet, basename='servicehandler'
)
router.register(r'alert', views.AlertHistoryViewSet, basename='alert')
router.register(
    r'unrecognized-neighbor',
    views.UnrecognizedNeighborViewSet,
    basename='unrecognized-neighbor',
)
router.register(r'auditlog', auditlogapi.LogEntryViewSet, basename='auditlog')
router.register(r'module', views.ModuleViewSet, basename='module')
router.register(r'netboxentity', views.NetboxEntityViewSet, basename='netboxentity')


urlpatterns = [
    path('', views.api_root),
    path('token/', views.get_or_create_token, name="token"),
    path('version/', views.get_nav_version, name="version"),
    path('prefix/routed/', views.RoutedPrefixList.as_view(), name="prefix-routed-list"),
    path('prefix/usage/', views.PrefixUsageList.as_view(), name="prefix-usage-list"),
    re_path(
        r"^prefix/usage/(?P<prefix>.*)$",
        views.PrefixUsageDetail.as_view(),
        name="prefix-usage-detail",
    ),
    path('', include(router.urls)),
    path('vendor/', views.VendorLookup.as_view(), name='vendor'),
    path('jwt/refresh/', views.JWTRefreshViewSet.as_view(), name='jwt-refresh'),
]
