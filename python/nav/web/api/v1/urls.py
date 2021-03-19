#
# Copyright (C) 2013 Uninett AS
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
# pylint: disable=E1101
"""Urlconf for the NAV REST api"""

from django.conf.urls import url, include
from rest_framework import routers

from nav.auditlog import api as auditlogapi
from nav.web.api.v1 import views

router = routers.SimpleRouter()
router.register(r'account', views.AccountViewSet)
router.register(r'accountgroup', views.AccountGroupViewSet, base_name='accountgroup')
router.register(r'rack', views.RackViewSet)
router.register(r'room', views.RoomViewSet)
router.register(r'location', views.LocationViewSet)
router.register(
    r'management-profile',
    views.ManagementProfileViewSet,
    base_name="management-profile",
)
router.register(r'netbox', views.NetboxViewSet)
router.register(r'interface', views.InterfaceViewSet)
router.register(r'prefix', views.PrefixViewSet)
router.register(r'vlan', views.VlanViewSet)
router.register(r'cabling', views.CablingViewSet, base_name='cabling')
router.register(r'patch', views.PatchViewSet, base_name='patch')
router.register(r'cam', views.CamViewSet, base_name='cam')
router.register(r'arp', views.ArpViewSet, base_name='arp')
router.register(
    r'servicehandler', views.ServiceHandlerViewSet, base_name='servicehandler'
)
router.register(r'alert', views.AlertHistoryViewSet, base_name='alert')
router.register(
    r'unrecognized-neighbor',
    views.UnrecognizedNeighborViewSet,
    base_name='unrecognized-neighbor',
)
router.register(r'auditlog', auditlogapi.LogEntryViewSet, base_name='auditlog')


urlpatterns = [
    url(r'^$', views.api_root),
    url(r'^token/$', views.get_or_create_token, name="token"),
    url(r'^version/$', views.get_nav_version, name="version"),
    url(
        r"^prefix/routed/?$",
        views.RoutedPrefixList.as_view(),
        name="prefix-routed-list",
    ),
    url(r"^prefix/usage/?$", views.PrefixUsageList.as_view(), name="prefix-usage-list"),
    url(
        r"^prefix/usage/(?P<prefix>.*)$",
        views.PrefixUsageDetail.as_view(),
        name="prefix-usage-detail",
    ),
    url(r'^', include(router.urls)),
]
