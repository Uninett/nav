#
# Copyright (C) 2013 UNINETT AS
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
# pylint: disable=E1101
"""Urlconf for the NAV REST api"""

from nav.web.api.v1 import views
from django.conf.urls import url, patterns, include
from rest_framework import routers

router = routers.SimpleRouter()
router.register(r'room', views.RoomViewSet)
router.register(r'netbox', views.NetboxViewSet)
router.register(r'interface', views.InterfaceViewSet)
router.register(r'prefix', views.PrefixViewSet)
router.register(r'cam', views.CamViewSet, base_name='cam')
router.register(r'arp', views.ArpViewSet, base_name='arp')

urlpatterns = patterns(
    "",
    url(r'^$', views.api_root),
    url(r'^', include(router.urls)),
    url(r'^token/$', views.get_or_create_token, name="token"),
    url(r"^prefix/routed/?$", views.RoutedPrefixList.as_view(),
        name="prefix-routed-list"),
    url(r"^prefix/usage/?$", views.PrefixUsageList.as_view(),
        name="prefix-usage-list"),
    url(r"^prefix/usage/(?P<prefix>.*)$", views.PrefixUsageDetail.as_view(),
        name="prefix-usage-detail"),
)
