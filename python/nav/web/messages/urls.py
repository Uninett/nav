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
"""Django URL configuration for messages tool"""

from django.urls import re_path

from nav.web.messages import views
from nav.web.messages.feeds import ActiveMessagesFeed

urlpatterns = [
    re_path(r'^$', views.redirect_to_active),
    re_path(r'^active/$', views.active, name='messages-home'),
    re_path(r'^create/$', views.save, name='messages-create'),
    re_path(r'^edit/(?P<message_id>\d+)$', views.save, name='messages-edit'),
    re_path(r'^active/$', views.active, name='messages-active'),
    re_path(r'^scheduled/$', views.planned, name='messages-planned'),
    re_path(r'^archive/$', views.historic, name='messages-historic'),
    re_path(r'^view/(?P<message_id>\d+)$', views.view, name='messages-view'),
    re_path(r'^expire/(?P<message_id>\d+)$', views.expire, name='messages-expire'),
    re_path(r'^followup/(?P<message_id>\d+)$', views.followup, name='messages-followup'),
    re_path(r'^rss/$', ActiveMessagesFeed(), name='messages-rss'),
]
