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
"""Django URL configuration for messages tool"""

from django.urls import path

from nav.web.messages import views
from nav.web.messages.feeds import ActiveMessagesFeed

urlpatterns = [
    path('', views.redirect_to_active),
    path('active/', views.active, name='messages-home'),
    path('create/', views.save, name='messages-create'),
    path('edit/<int:message_id>', views.save, name='messages-edit'),
    path('active/', views.active, name='messages-active'),
    path('scheduled/', views.planned, name='messages-planned'),
    path('archive/', views.historic, name='messages-historic'),
    path('view/<int:message_id>', views.view, name='messages-view'),
    path('expire/<int:message_id>', views.expire, name='messages-expire'),
    path('followup/<int:message_id>', views.followup, name='messages-followup'),
    path('rss/', ActiveMessagesFeed(), name='messages-rss'),
]
