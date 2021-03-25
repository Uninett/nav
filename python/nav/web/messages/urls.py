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

from django.conf.urls import url

from nav.web.messages import views
from nav.web.messages.feeds import ActiveMessagesFeed

urlpatterns = [
    url(r'^$', views.redirect_to_active),
    url(r'^active/$', views.active, name='messages-home'),
    url(r'^create/$', views.save, name='messages-create'),
    url(r'^edit/(?P<message_id>\d+)$', views.save, name='messages-edit'),
    url(r'^active/$', views.active, name='messages-active'),
    url(r'^scheduled/$', views.planned, name='messages-planned'),
    url(r'^archive/$', views.historic, name='messages-historic'),
    url(r'^view/(?P<message_id>\d+)$', views.view, name='messages-view'),
    url(r'^expire/(?P<message_id>\d+)$', views.expire, name='messages-expire'),
    url(r'^followup/(?P<message_id>\d+)$', views.followup, name='messages-followup'),
    url(r'^rss/$', ActiveMessagesFeed(), name='messages-rss'),
]
